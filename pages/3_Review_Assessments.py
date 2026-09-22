"""Review Assessments page - grading, result download, and result emailing."""
import io
import json

import streamlit as st

import database as db
from email_service import EmailDeliveryError, candidate_result_filename, send_candidate_result
from question_types import QUESTION_TYPE_SECTION_LABELS, REVIEWER_SCORED_TYPES
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_submissions,
    clear_read_caches,
    result_table,
    format_result_datetime,
)

st.set_page_config(
    page_title="Review Assessments - CTA Portal",
    page_icon=":material/rate_review:",
    layout="centered",
)
inject_global_styles()

user = require_login()
if user["role"] not in ("Admin", "Reviewer"):
    st.error("Access denied.")
    st.stop()

sidebar_nav(user)
render_logo()
st.title("Competency Technical Assessment (CTA) Portal")
st.subheader("Assessment review")

# Consume one-shot flags set before st.rerun().
if st.session_state.pop("show_finalized_assessment", False):
    st.session_state.assessment_review_status = "Graded"
finalized_assessment = st.session_state.pop("assessment_finalized", None)
if finalized_assessment:
    st.success(f"Assessment finalized successfully for {finalized_assessment['candidate_name']}.")

rows = cached_submissions(user["id"])
left, right = st.columns(2)
left.metric("Pending review", sum(r["status"] == "Pending Review" for r in rows))
right.metric("Graded", sum(r["status"] == "Graded" for r in rows))

status = st.selectbox(
    "Status",
    ["All", "Pending Review", "Graded"],
    index=1,
    key="assessment_review_status",
)
rows = [r for r in rows if status == "All" or r["status"] == status]

if not rows:
    st.info("No assessments match this view.")
    st.stop()

table = result_table(rows)

st.markdown(
    """<style>
    [data-testid="stExpander"] details summary p { font-size: 1rem; }
    @media (max-width: 640px) {
        [data-testid="stExpander"] details summary p { font-size: .92rem; }
        [data-testid="stMarkdownContainer"] p { overflow-wrap: anywhere; }
    }
    </style>""",
    unsafe_allow_html=True,
)

# Paginate summary list.
page_size = 15
total_pages = max(1, (len(table) + page_size - 1) // page_size)
if total_pages > 1:
    p_col1, p_col2 = st.columns([1, 3])
    with p_col1:
        page_num = st.number_input(
            "Page", min_value=1, max_value=total_pages, value=1, step=1, key="ar_page"
        )
    with p_col2:
        st.caption(
            f"Showing submissions {(page_num - 1) * page_size + 1} "
            f"to {min(page_num * page_size, len(table))} of {len(table)}"
        )
    page_table = table[(page_num - 1) * page_size: page_num * page_size]
else:
    page_table = table

for result_row in page_table:
    summary = f"{result_row['Candidate']} · {result_row['Discipline']} · {result_row['Status']}"
    with st.expander(summary, expanded=False):
        for label, value in result_row.items():
            st.markdown(f"**{label}:** {value if value != '' else chr(8212)}")

# Assessment selector and detail grading panel.
sid = st.selectbox(
    "Assessment",
    [r["id"] for r in rows],
    format_func=lambda v: next(
        f"#{r['id']} · {r['candidate_name']} · {r['discipline']}" for r in rows if r["id"] == v
    ),
)
sub = next(r for r in rows if r["id"] == sid)


def _candidate_result_pdf(sub: dict) -> bytes:
    """Build a branded PDF result report in memory."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=27 * mm, leftMargin=27 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CATTitle", parent=styles["Title"],
                              textColor=colors.HexColor("#B51F2D"), fontSize=20, leading=24, spaceAfter=8))
    styles.add(ParagraphStyle(name="CATBody", parent=styles["BodyText"],
                              fontSize=10, leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="CATResultHeading", parent=styles["Heading2"],
                              textColor=colors.HexColor("#142735"), fontSize=11, leading=14,
                              alignment=1, spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name="CATOverallResult", parent=styles["CATResultHeading"],
                              alignment=1, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="CATExplainHeading", parent=styles["BodyText"],
                              textColor=colors.HexColor("#142735"), fontSize=8, leading=10,
                              spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyle(name="CATExplainBody", parent=styles["BodyText"],
                              textColor=colors.HexColor("#4B5563"), fontSize=8, leading=10, spaceAfter=0))
    styles.add(ParagraphStyle(name="CATCompany", parent=styles["CATBody"],
                              alignment=1, fontSize=7, leading=9, textColor=colors.HexColor("#4B5563")))

    logo_path = "img/C.A.T. Logo - Horizontal.jpg"
    logo_width = 35.1 * mm
    logo_source_width, logo_source_height = ImageReader(logo_path).getSize()
    logo_height = logo_width * logo_source_height / logo_source_width
    story = [
        Image(logo_path, width=logo_width, height=logo_height),
        Paragraph(
            "<b>QUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.</b><br/>"
            "Ash Shulah, Dammam 34266, Saudi Arabia",
            styles["CATCompany"],
        ),
        Spacer(1, 2 * mm),
        Paragraph("Candidate Assessment Result", styles["CATTitle"]),
        Spacer(1, 4 * mm),
    ]
    story.append(
        Paragraph(
            f"<b>Candidate:</b> {sub.get('candidate_name', '')}<br/>"
            f"<b>Iqama No:</b> {sub.get('iqama_no', '')}<br/>"
            f"<b>Discipline:</b> {sub.get('discipline', '')}<br/>"
            f"<b>Exam date:</b> {format_result_datetime(sub.get('exam_date', ''))}",
            styles["CATBody"],
        )
    )
    if sub["status"] != "Graded":
        story.append(Paragraph("<b>Overall result:</b> Pending Review", styles["CATOverallResult"]))
    else:
        rows_data = [["Question type", "Weight", "Weighted grade"]]
        for kind, label in (("mcq", "Multiple Choice"), ("essay", "Essay"), ("oral_practical", "Oral-Practical")):
            rows_data.append([label, f"{db.GRADE_WEIGHTS[kind]}%",
                               f"{db.weighted_category_percentage(sub, kind):.1f}%"])
        overall_pct = db.final_percentage(sub)
        overall_status = "PASS" if overall_pct >= 70 else "FAIL"
        overall_color = "#188038" if overall_status == "PASS" else "#B51F2D"
        story += [
            Spacer(1, 4 * mm),
            Paragraph("Results by question type", styles["CATResultHeading"]),
            Table(
                rows_data,
                colWidths=[35 * mm, 23 * mm, 30 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B51F2D")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DCDE")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEADING", (0, 0), (-1, -1), 10),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]),
            ),
            Spacer(1, 5 * mm),
            Paragraph(
                f"<b>Overall result:</b> {overall_pct:.1f}% - "
                f'<font color="{overall_color}"><b>{overall_status}</b></font>',
                styles["CATOverallResult"],
            ),
        ]
    story += [
        Spacer(1, 6 * mm),
        Paragraph("<b>How pass/fail is determined</b>", styles["CATExplainHeading"]),
        Paragraph(
            "The final grade is calculated from the weighted question-type grades: "
            "Multiple Choice 60%, Essay 20%, and Oral-Practical 20%. "
            "The candidate must achieve at least 70% in the final grade. "
            "A result remains Pending Review until the Reviewer scores all Essay and Oral-Practical responses.",
            styles["CATExplainBody"],
        ),
    ]
    doc.build(story)
    return output.getvalue()


try:
    result_pdf = _candidate_result_pdf(sub)
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        result_filename = candidate_result_filename(sub.get("candidate_name", "Candidate"))
        st.download_button(
            "Download Candidate Result", result_pdf, result_filename,
            "application/pdf", use_container_width=True,
        )
    with action_col2:
        if st.button("Email Result to Candidate", type="primary", use_container_width=True):
            if not sub.get("email"):
                st.error("This candidate does not have an email address.")
            else:
                try:
                    send_candidate_result(
                        sub["email"], sub.get("candidate_name", "Candidate"), result_pdf
                    )
                    st.success(f"Result emailed to {sub['email']}.")
                except (EmailDeliveryError, OSError, ValueError) as exc:
                    st.error(str(exc))
except (ImportError, OSError, ValueError) as exc:
    st.error(
        f"Unable to create the candidate result PDF. Install the reportlab package and retry. Details: {exc}"
    )

# Grading panel.
answers = db.answer_details(user["id"], sid)
questionnaire = st.expander("Questionnaire", expanded=False)
questionnaire.__enter__()

with st.form(f"grading_{sid}"):
    scores = {}
    observed_responses = {}
    question_section = None
    question_section_type = None

    for a in answers:
        q = json.loads(a["snapshot"])
        if q["q_type"] != question_section_type:
            if question_section is not None:
                question_section.__exit__(None, None, None)
            question_section_type = q["q_type"]
            section_title = QUESTION_TYPE_SECTION_LABELS.get(q["q_type"], "Questions")
            question_section = st.expander(section_title, expanded=False)
            question_section.__enter__()

        question_type = {
            "mcq": "Multiple Choice Question",
            "essay": "Essay",
            "oral_practical": "Oral-Practical",
        }.get(q["q_type"], q["q_type"])
        st.write(f"{question_type}: {q['question_text']}")

        if q["q_type"] in REVIEWER_SCORED_TYPES:
            if q["q_type"] == "essay":
                st.text_area(
                    "Candidate response", value=a["submitted_answer"], disabled=True,
                    height=160, key=f"response_{a['id']}",
                )
            else:
                observed_responses[a["id"]] = st.text_area(
                    "Observed response", value=a["submitted_answer"], height=120,
                    key=f"observed_response_{a['id']}", disabled=sub["status"] == "Graded",
                )
            st.info(f"Scoring guidance: {q['rubric']}")
            score_max = min(q["max_points"], 10)
            scores[a["id"]] = st.number_input(
                f"Points for answer #{a['id']} (max {int(score_max)})",
                min_value=0, max_value=int(score_max),
                value=min(int(a["awarded_score"]), int(score_max)),
                step=1, disabled=sub["status"] == "Graded",
            )
        else:
            st.caption(f"Correct answer: {q['correct_answer']} · Awarded: {a['awarded_score']:g}")

    if question_section is not None:
        question_section.__exit__(None, None, None)

    comments = st.text_area(
        "Reviewer feedback", value=sub["reviewer_comments"] or "",
        disabled=sub["status"] == "Graded",
    )
    if st.form_submit_button(
        "Finalize grade", disabled=sub["status"] == "Graded", type="primary"
    ):
        try:
            db.grade(user["id"], sid, scores, comments, observed_responses)
            clear_read_caches()
            st.session_state.assessment_finalized = {"candidate_name": sub["candidate_name"]}
            st.session_state.show_finalized_assessment = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

questionnaire.__exit__(None, None, None)

if sub["status"] == "Graded":
    st.subheader("CTA Results")
    with st.expander("Results by Question Type", expanded=True):
        for kind, label in (
            ("mcq", "Multiple Choice"),
            ("essay", "Essay"),
            ("oral_practical", "Oral-Practical"),
        ):
            max_grade = db.GRADE_WEIGHTS[kind]
            score = db.weighted_category_percentage(sub, kind)
            st.info(f"{label} (Grade Weight {max_grade}%) : {score:.2f}%")
    with st.expander("Final Result", expanded=True):
        final_grade = db.result(sub)
        (st.success if final_grade.startswith("PASS") else st.error)(f"Final Grade: {final_grade}")

