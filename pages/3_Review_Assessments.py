"""Review Assessments page - grading, result download, and result emailing."""
import io
import json
from datetime import date

import streamlit as st

import database as db
import assessment_analysis
from email_service import EmailDeliveryError, candidate_result_filename, send_candidate_result
from question_types import QUESTION_TYPES, QUESTION_TYPE_SECTION_LABELS, REVIEWER_SCORED_TYPES
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_questions,
    cached_projects,
    cached_submission_review_candidates,
    cached_submission_page,
    cached_submission_status_counts,
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

db.ensure_employment_verification_schema()
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

status_counts = cached_submission_status_counts(user["id"])
left, right = st.columns(2)
left.metric("Pending review", status_counts.get("Pending Review", 0))
right.metric("Graded", status_counts.get("Graded", 0))

saved_drafts = db.assessment_drafts_for_review(user["id"])
if saved_drafts:
    question_banks = {}
    with st.expander("Saved in-progress answers", expanded=True):
        st.caption(
            "Saved responses are read-only drafts. They are not submitted and cannot be scored until the candidate submits."
        )
        for draft in saved_drafts:
            payload = draft["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            saved_responses = payload.get("assessment_responses") or {}
            if not isinstance(saved_responses, dict):
                saved_responses = {}
            mcq_ids = payload.get("assessment_mcq_ids") or []
            essay_ids = payload.get("assessment_essay_ids") or []
            response_count = sum(
                bool(str(saved_responses.get(str(qid), saved_responses.get(qid, ""))).strip())
                for qid in [*mcq_ids, *essay_ids]
            )
            phase = str(payload.get("assessment_phase", "mcq")).replace("_", " ").title()
            draft_title = (
                f"{draft['candidate_name']} · {draft['discipline']} · {phase} · "
                f"{response_count} saved responses · {format_result_datetime(draft['updated_at'])}"
            )
            with st.expander(draft_title, expanded=False):
                if draft["discipline"] not in question_banks:
                    question_banks[draft["discipline"]] = {
                        q["id"]: q for q in cached_questions(draft["discipline"], include_inactive=True)
                    }
                questions_by_id = question_banks[draft["discipline"]]
                for kind, label, question_ids in (
                    ("mcq", "Multiple Choice", mcq_ids),
                    ("essay", "Essay", essay_ids),
                ):
                    if not question_ids:
                        continue
                    st.markdown(f"**{label} saved responses**")
                    for number, question_id in enumerate(question_ids, 1):
                        question = questions_by_id.get(question_id)
                        question_text = question["question_text"] if question else f"Question {question_id} is no longer available in the question bank."
                        answer = saved_responses.get(str(question_id), saved_responses.get(question_id, ""))
                        st.write(f"{number}. {question_text}")
                        if kind == "essay":
                            st.text_area(
                                f"Saved essay response {number}", value=str(answer), disabled=True,
                                key=f"saved_draft_essay_{draft['candidate_id']}_{question_id}",
                            )
                        else:
                            st.caption(f"Saved answer: {answer if str(answer).strip() else 'No answer saved'}")

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

submissions = cached_submission_review_candidates(user["id"])
disciplines = sorted({str(row.get("discipline") or "") for row in submissions if row.get("discipline")})
projects = sorted(
    {
        str(row.get("project_assignment") or "").strip() or "Unassigned"
        for row in submissions
    },
    key=str.casefold,
)
assessment_dates = sorted(
    {str(row.get("exam_date") or "")[:10] for row in submissions if row.get("exam_date")},
    reverse=True,
)

st.markdown("#### Find an assessment")
filter_status, filter_name, filter_date = st.columns([1, 1.5, 1.2])
with filter_status:
    status = st.selectbox(
        "Status",
        ["All", "Pending Review", "Graded"],
        index=1,
        key="assessment_review_status",
    )
with filter_name:
    candidate_name_filter = st.text_input("Name", placeholder="Search candidate name")
with filter_date:
    assessment_date = st.selectbox("Assessment Date", ["All dates", *assessment_dates])

filter_project, filter_discipline, _ = st.columns([1, 1.3, 1.4])
with filter_project:
    project = st.selectbox("Project", ["All projects", *projects])
with filter_discipline:
    discipline = st.selectbox("Discipline", ["All disciplines", *disciplines])

search_name = candidate_name_filter.strip().casefold()
filtered_rows = [
    row for row in submissions
    if (status == "All" or row.get("status") == status)
    and (
        project == "All projects"
        or (str(row.get("project_assignment") or "").strip() or "Unassigned") == project
    )
    and (discipline == "All disciplines" or row.get("discipline") == discipline)
    and (not search_name or search_name in str(row.get("candidate_name") or "").casefold())
    and (
        assessment_date == "All dates"
        or str(row.get("exam_date") or "")[:10] == assessment_date
    )
]

st.caption(f"{len(filtered_rows)} assessment{'s' if len(filtered_rows) != 1 else ''} found")
if not filtered_rows:
    st.session_state.pop("assessment_candidate_selection", None)
    st.info("No assessments match these filters. Adjust or clear a filter to see more candidates.")
    st.stop()

candidate_labels = {}
label_counts = {}
for row in filtered_rows:
    label = f"{row.get('candidate_name') or 'Unknown candidate'} · {row.get('discipline') or 'No discipline'}"
    label_counts[label] = label_counts.get(label, 0) + 1
    candidate_labels[row["id"]] = label
for row in filtered_rows:
    label = candidate_labels[row["id"]]
    if label_counts[label] > 1:
        candidate_labels[row["id"]] = (
            f"{label} · {str(row.get('exam_date') or '')[:10]} · Assessment #{row['id']}"
        )

st.markdown("#### Select candidate")
with st.container(height=265, border=True):
    sid = st.radio(
        "Candidate · Discipline",
        [row["id"] for row in filtered_rows],
        format_func=lambda submission_id: candidate_labels[submission_id],
        key="assessment_candidate_selection",
    )

_, selected_rows = cached_submission_page(user["id"], limit=1, submission_id=sid)
if not selected_rows:
    st.error("This assessment is no longer available. Refresh the page and select it again.")
    st.stop()
sub = selected_rows[0]
st.divider()
candidate_heading, status_heading = st.columns([3, 1])
with candidate_heading:
    st.subheader(sub.get("candidate_name") or "Unknown candidate")
    st.caption(sub.get("discipline") or "No discipline")
with status_heading:
    st.metric("Review status", sub["status"])

project_options = ["Unassigned", *[p for p in cached_projects(user["id"]) if p != "Unassigned"]]
current_project = str(sub.get("project_assignment") or "").strip() or "Unassigned"
if current_project not in project_options:
    project_options.append(current_project)
project_col, project_action_col = st.columns([3, 1])
with project_col:
    selected_project = st.selectbox(
        "Assessment project",
        project_options,
        index=project_options.index(current_project),
        key=f"assessment_project_{sub['id']}",
        help="This changes only the selected assessment, not the candidate's schedule.",
    )
with project_action_col:
    st.write("")
    st.write("")
    save_project = st.button("Save project", key=f"save_assessment_project_{sub['id']}")
if save_project:
    try:
        db.update_assessment_project(
            user["id"], sub["id"], selected_project,
        )
        clear_read_caches()
        st.session_state.assessment_candidate_selection = sub["id"]
        st.success("Assessment project updated.")
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))

detail_columns = st.columns(4)
detail_columns[0].markdown(f"**Assessment date**  \n{format_result_datetime(sub.get('exam_date')) or '—'}")
detail_columns[1].markdown(f"**Job title**  \n{sub.get('designation') or '—'}")
detail_columns[2].markdown(f"**Employee number**  \n{sub.get('employee_no') or '—'}")
detail_columns[3].markdown(
    f"**Graded**  \n{format_result_datetime(sub.get('graded_at')) or 'Not graded'}"
)
if sub.get("reviewer_comments"):
    st.markdown(f"**Reviewer feedback**  \n{sub['reviewer_comments']}")


@st.cache_data(show_spinner=False)
def _candidate_result_pdf(sub: dict, answers: list = None) -> bytes:
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
    if answers:
        try:
            pdf_analysis = db.assessment_report(user["id"], sub)
            if pdf_analysis.get("subjects"):
                story += [
                    Spacer(1, 4 * mm),
                    Paragraph("Technical Subject Competency", styles["CATResultHeading"]),
                ]
                subj_rows = [["Technical Subject", "Score", "Evaluation"]]
                for s in pdf_analysis["subjects"][:6]:
                    subj_rows.append([s["subject"][:32], f"{s['percentage']:.1f}%", s["status"]])
                story.append(
                    Table(
                        subj_rows,
                        colWidths=[65 * mm, 20 * mm, 45 * mm],
                        style=TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#142735")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9DCDE")),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 7),
                            ("LEADING", (0, 0), (-1, -1), 9),
                            ("PADDING", (0, 0), (-1, -1), 3),
                        ]),
                    )
                )
            if pdf_analysis.get("strengths"):
                str_text = ", ".join(t["sub_subject"] for t in pdf_analysis["strengths"][:3])
                story.append(Spacer(1, 2 * mm))
                story.append(Paragraph(f"<b>Demonstrated Strengths:</b> {str_text}", styles["CATExplainBody"]))
            if pdf_analysis.get("development_areas"):
                gap_text = ", ".join(t["sub_subject"] for t in pdf_analysis["development_areas"][:3])
                story.append(Spacer(1, 1 * mm))
                story.append(Paragraph(f"<b>Development Focus Areas:</b> {gap_text}", styles["CATExplainBody"]))
        except Exception:
            pass
    story += [
        Spacer(1, 6 * mm),
        Paragraph("<b>How pass/fail is determined</b>", styles["CATExplainHeading"]),
        Paragraph(
            "The final grade is calculated from the weighted question-type grades: "
            "Multiple Choice 60%, Essay 20%, and Oral-Practical 20%. "
            "The candidate must achieve at least 70% in the final grade. "
            "A result remains Pending Review until the Reviewer scores all Essay and Oral-Practical responses.",
        ),
    ]
    
    # Confidentiality Agreement Section
    story += [
        Spacer(1, 6 * mm),
        Paragraph("<b>Confidentiality Agreement</b>", styles["CATExplainHeading"]),
    ]
    conf_notice = (
        "This result and all related assessment information are confidential and remain subject to the "
        "confidentiality agreement accepted at first login. Do not forward, publish, copy, record, photograph, "
        "or share this result or any assessment questions or answers with anyone who is not authorized to handle the assessment."
    )
    if sub.get("conf_agreement_version"):
        accepted_time = format_result_datetime(sub.get("conf_acceptance_time", ""))
        conf_notice += (
            f"<br/><br/>This notice confirms the existing agreement (Version {sub.get('conf_agreement_version')}, "
            f"accepted {accepted_time} Saudi Arabia Time) and does not require another acceptance."
        )
    story.append(Paragraph(conf_notice, styles["CATExplainBody"]))

    doc.build(story)
    return output.getvalue()


# Load answers and compute auto analysis
answers = db.answer_details(user["id"], sid)
analysis = db.assessment_report(user["id"], sub)

try:
    result_pdf = _candidate_result_pdf(sub, answers)
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        result_filename = candidate_result_filename(sub.get("candidate_name", "Candidate"))
        st.download_button(
            "Download Candidate Result", result_pdf, result_filename,
            "application/pdf", width="stretch",
        )
    with action_col2:
        if st.button("Email Result to Candidate", type="primary", width="stretch"):
            if not sub.get("email"):
                st.error("This candidate does not have an email address.")
            else:
                try:
                    send_candidate_result(
                        sub["email"], sub.get("candidate_name", "Candidate"), result_pdf, sub.get("conf_agreement_version")
                    )
                    st.success(f"Result emailed to {sub['email']}.")
                except (EmailDeliveryError, OSError, ValueError) as exc:
                    st.error(str(exc))
except (ImportError, OSError, ValueError) as exc:
    st.error(
        f"Unable to create the candidate result PDF. Install the reportlab package and retry. Details: {exc}"
    )

# Grading panel.
questionnaire = st.expander("Questionnaire", expanded=False)
questionnaire.__enter__()

with st.form(f"grading_{sid}"):
    scores = {}
    observed_responses = {}
    question_section = None
    question_section_type = None
    oral_practical_number = 0
    essay_number = 0
    oral_practical_numbers = {}
    scored_question_numbers = {}

    question_type_order = {kind: idx for idx, kind in enumerate(QUESTION_TYPES)}
    grouped_answers = sorted(
        answers,
        key=lambda a: (
            question_type_order.get(
                (json.loads(a["snapshot"]) if isinstance(a["snapshot"], str) else a["snapshot"]).get("q_type"),
                len(QUESTION_TYPES),
            ),
            a.get("id", 0),
        ),
    )

    for a in grouped_answers:
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
                essay_number += 1
                scored_question_numbers[a["id"]] = ("Essay", essay_number)
                st.text_area(
                    "Candidate response", value=a["submitted_answer"], disabled=True,
                    height=160, key=f"response_{a['id']}",
                )
            else:
                oral_practical_number += 1
                oral_practical_numbers[a["id"]] = oral_practical_number
                scored_question_numbers[a["id"]] = ("Oral-Practical", oral_practical_number)
                observed_responses[a["id"]] = st.text_area(
                    "Observed response", value=a["submitted_answer"], height=120,
                    key=f"observed_response_{a['id']}", disabled=sub["status"] == "Graded",
                )
            st.info(f"Scoring guidance: {q['rubric']}")
            score_max = min(q["max_points"], 10)
            scores[a["id"]] = st.number_input(
                f"Points for {scored_question_numbers[a['id']][0]} question {scored_question_numbers[a['id']][1]} (max {score_max:g})",
                min_value=0.0, max_value=float(score_max),
                value=(
                    min(float(a["awarded_score"]), float(score_max))
                    if sub["status"] == "Graded"
                    else None
                ),
                step=0.1, format="%.1f", key=f"review_score_{sid}_{a['id']}",
                disabled=sub["status"] == "Graded",
            )
        else:
            st.caption(f"Correct answer: {q['correct_answer']} · Awarded: {a['awarded_score']:g}")

    if question_section is not None:
        question_section.__exit__(None, None, None)

    finalize_grade = st.form_submit_button(
        "Finalize grade", disabled=sub["status"] == "Graded", type="primary"
    )

questionnaire.__exit__(None, None, None)

# Automated Candidate Analysis
with st.expander("Automated Candidate Analysis", expanded=(sub["status"] == "Graded")):
    assessment_analysis.render_assessment_analysis(analysis, allow_feedback_copy=True, for_candidate=False)

if sub["status"] != "Graded":
    if st.button("Apply Auto-Analysis Summary to Reviewer Feedback", key=f"apply_auto_fb_{sid}"):
        st.session_state[f"review_comments_{sid}"] = analysis.get("reviewer_feedback_snippet", "")
        st.rerun()

comments = st.text_area(
    "Additional Reviewer Feedback",
    value=st.session_state.get(f"review_comments_{sid}", sub["reviewer_comments"] or ""),
    key=f"review_comments_{sid}", disabled=sub["status"] == "Graded",
    help="Add your observations and recommendations. This feedback is saved when you finalize the grade.",
)

if finalize_grade:
    unanswered_oral_numbers = [
        ("Oral-Practical", number, "observed response")
        for answer_id, number in oral_practical_numbers.items()
        if not str(observed_responses.get(answer_id, "")).strip()
    ]
    ungraded_numbers = [
        (kind, number, "score")
        for answer_id, (kind, number) in scored_question_numbers.items()
        if scores.get(answer_id) is None
    ]
    pending_items = unanswered_oral_numbers + ungraded_numbers
    if pending_items:
        st.session_state[f"pending_review_blanks_{sid}"] = pending_items
        st.rerun()
    else:
        try:
            db.grade(user["id"], sid, scores, comments, observed_responses)
            clear_read_caches()
            st.session_state.assessment_finalized = {"candidate_name": sub["candidate_name"]}
            st.session_state.show_finalized_assessment = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

pending_review_blanks = st.session_state.get(f"pending_review_blanks_{sid}")
if pending_review_blanks:
    blank_descriptions = [
        f"{kind} question {number} ({field} blank)"
        for kind, number, field in pending_review_blanks
    ]
    st.warning(
        "Incomplete grading: "
        + "; ".join(blank_descriptions)
        + ". Return to grading to complete these fields, or finalize with blank scores set to zero."
    )
    return_col, proceed_col = st.columns(2)
    if return_col.button("Return to grading", key=f"return_review_grade_{sid}", type="primary"):
        st.session_state.pop(f"pending_review_blanks_{sid}", None)
        st.rerun()
    if proceed_col.button("Finalize with blank scores set to zero", key=f"proceed_review_grade_{sid}"):
        st.session_state.pop(f"pending_review_blanks_{sid}", None)
        for answer_id, score in list(scores.items()):
            if score is None:
                scores[answer_id] = 0
        try:
            db.grade(user["id"], sid, scores, comments, observed_responses)
            clear_read_caches()
            st.session_state.assessment_finalized = {"candidate_name": sub["candidate_name"]}
            st.session_state.show_finalized_assessment = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

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

st.subheader("Grading summary")
summary = result_table([sub])[0]
st.table([{"Assessment detail": label, "Result": value or "—"} for label, value in summary.items()])

verification_history = db.employment_verification_history_for_assessment(user["id"], sid)
st.subheader("Employment Verification")
st.caption("Employment verification is recorded separately and does not change the CTA result.")

if st.session_state.pop("employment_verification_saved", False):
    st.success("Employment verification update recorded.")

latest_verification = verification_history[0] if verification_history else {}
if user["role"] == "Admin" and sub.get("user_id") is not None:
    statuses = list(db.EMPLOYMENT_VERIFICATION_STATUSES)
    with st.form(f"employment_verification_{sid}"):
        verification_status = st.selectbox(
            "Verification status",
            statuses,
            index=(
                statuses.index(latest_verification["status"])
                if latest_verification.get("status") in statuses else 0
            ),
        )
        verification_date = st.date_input(
            "Verification or finding date",
            value=latest_verification.get("verification_date") or date.today(),
        )
        evidence_source = st.text_input(
            "Evidence source",
            value=latest_verification.get("evidence_source") or "",
            max_chars=1000,
            help="For example, issuing organization confirmation or a documented verification response.",
        )
        verification_notes = st.text_area(
            "Review notes",
            value=latest_verification.get("notes") or "",
            max_chars=5000,
            help="Record factual observations and the basis for the verification status.",
        )
        verification_outcome = st.text_area(
            "Outcome or follow-up",
            value=latest_verification.get("outcome") or "",
            max_chars=2000,
            help="Record the verification outcome or next action, not an assessment grade.",
        )
        save_verification = st.form_submit_button("Record update", type="primary")

    if save_verification:
        try:
            db.record_employment_verification(
                user["id"],
                sub["user_id"],
                verification_status,
                verification_date,
                evidence_source,
                verification_notes,
                verification_outcome,
            )
            st.session_state.employment_verification_saved = True
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))
elif user["role"] == "Admin":
    st.info("Verification updates are unavailable because this assessment has no linked candidate account.")

if not verification_history:
    st.info("No employment verification updates recorded.")
else:
    for verification in verification_history:
        details = (
            f"**Verification date:** {format_result_datetime(verification['verification_date']) or '—'}\n\n"
            f"**Evidence source:** {verification['evidence_source'] or '—'}\n\n"
            f"**Review notes:** {verification['notes'] or '—'}\n\n"
            f"**Outcome or follow-up:** {verification['outcome'] or '—'}\n\n"
            f"**Recorded by:** {verification['recorded_by_name']} · "
            f"{format_result_datetime(verification['created_at'])}"
        )
        if verification["status"] == "Adverse finding":
            st.error(f"**Adverse finding**\n\n{details}")
        else:
            st.info(f"**{verification['status']}**\n\n{details}")
