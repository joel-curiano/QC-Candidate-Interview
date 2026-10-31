"""Aggregate submitted assessment results and build analytics exports."""

from html import escape
from io import BytesIO
from pathlib import Path

import database as db
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from shared import result_table


LOGO_PATH = Path(__file__).parent / "img" / "C.A.T. Logo - Horizontal.jpg"


class NumberedCanvas(canvas.Canvas):
    """Draw a Page n of total footer after the complete report is built."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for page_number, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            if page_number > 1:
                self.setFillColor(colors.HexColor("#1E3A5F"))
                self.setFont("Helvetica-Bold", 9)
                self.drawString(12 * mm, A4[1] - 12 * mm, "Competency Technical Assessment (CTA)")
                self.drawRightString(A4[0] - 12 * mm, A4[1] - 12 * mm, "C.A.T. International L.L.C.")
                self.setStrokeColor(colors.HexColor("#CBD5E1"))
                self.line(12 * mm, A4[1] - 16 * mm, A4[0] - 12 * mm, A4[1] - 16 * mm)
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.line(12 * mm, 13 * mm, A4[0] - 12 * mm, 13 * mm)
            self.setFillColor(colors.HexColor("#475569"))
            self.setFont("Helvetica", 8)
            self.drawRightString(A4[0] - 12 * mm, 8 * mm, f"Page {page_number} of {page_count}")
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def _empty_summary() -> dict:
    return {
        "total": 0,
        "graded": 0,
        "pending": 0,
        "passed": 0,
        "failed": 0,
        "score_total": 0.0,
    }


def _add_assessment(summary: dict, submission: dict) -> None:
    summary["total"] += 1
    result = db.result(submission)
    if result == "Pending Review":
        summary["pending"] += 1
        return

    outcome = result.split(" ", 1)[0]
    if outcome == "PASS":
        summary["passed"] += 1
    elif outcome == "FAIL":
        summary["failed"] += 1
    else:
        raise ValueError(f"Unexpected assessment result: {result}")

    summary["graded"] += 1
    summary["score_total"] += db.final_percentage(submission)


def _finish_summary(summary: dict) -> dict:
    graded = summary["graded"]
    passed = summary["passed"]
    failed = summary["failed"]
    score_total = summary["score_total"]
    return {
        "total": summary["total"],
        "graded": graded,
        "pending": summary["pending"],
        "passed": passed,
        "failed": failed,
        "pass_rate": 100 * passed / graded if graded else None,
        "fail_rate": 100 * failed / graded if graded else None,
        "average_score": score_total / graded if graded else None,
    }


def summarize_assessments(submissions: list[dict]) -> dict:
    """Summarize visible submissions overall and by their assigned project."""
    totals = _empty_summary()
    projects = {}

    for submission in submissions:
        project = str(submission.get("project_assignment") or "").strip() or "Unassigned"
        project_summary = projects.setdefault(project, _empty_summary())
        _add_assessment(totals, submission)
        _add_assessment(project_summary, submission)

    return {
        "totals": _finish_summary(totals),
        "projects": [
            {"project": project, **_finish_summary(summary)}
            for project, summary in sorted(projects.items(), key=lambda item: item[0].casefold())
        ],
    }


def _project_name(submission: dict) -> str:
    return str(submission.get("project_assignment") or "").strip() or "Unassigned"


def analytics_pdf_bytes(submissions: list[dict], selected_project: str) -> bytes:
    """Build a printable analytics report for all projects or one selected project."""
    filtered_submissions = (
        submissions
        if selected_project == "All projects"
        else [row for row in submissions if _project_name(row) == selected_project]
    )
    summary = summarize_assessments(filtered_submissions)
    totals = summary["totals"]
    styles = getSampleStyleSheet()
    normal = styles["BodyText"]
    normal.fontSize = 8
    normal.leading = 10
    header = ParagraphStyle(
        "TableHeader",
        parent=normal,
        fontName="Helvetica-Bold",
        textColor=colors.white,
        fontSize=8,
        leading=9,
    )

    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=20 * mm,
        bottomMargin=14 * mm,
        title="CTA Assessment Analytics",
        pageCompression=0,
    )
    logo = Image(str(LOGO_PATH), width=52 * mm, height=35 * mm)
    logo.hAlign = "CENTER"
    company_details = Paragraph(
        '<font color="#C81E2A"><b>QUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.</b></font><br/>'
        '<font color="#1E3A5F">Ash Shulah, Dammam 34266, Saudi Arabia</font>',
        ParagraphStyle("CompanyDetails", parent=styles["Normal"], alignment=1),
    )
    story = [
        logo,
        Spacer(1, 2 * mm),
        company_details,
        Spacer(1, 5 * mm),
        Paragraph(
            "Competency Technical Assessment (CTA) Portal",
            ParagraphStyle("PortalTitle", parent=styles["Title"], alignment=1),
        ),
        Paragraph("Assessment Analytics", styles["Heading2"]),
        Paragraph(f"Project: <b>{escape(selected_project)}</b>", styles["Normal"]),
        Spacer(1, 5 * mm),
    ]

    metric_rows = [
        ["Total assessments", "Graded", "Pending review", "Pass", "Fail"],
        [
            str(totals["total"]),
            str(totals["graded"]),
            str(totals["pending"]),
            str(totals["passed"]),
            str(totals["failed"]),
        ],
    ]
    metrics = Table(metric_rows, colWidths=[34 * mm] * 5)
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([metrics, Spacer(1, 6 * mm)])

    if selected_project == "All projects":
        story.append(Paragraph("Results by Project", styles["Heading2"]))
        project_data = [["Project", "Total", "Graded", "Pending", "Pass", "Fail", "Average grade"]]
        for row in summary["projects"]:
            project_data.append(
                [
                    row["project"],
                    str(row["total"]),
                    str(row["graded"]),
                    str(row["pending"]),
                    str(row["passed"]),
                    str(row["failed"]),
                    f'{row["average_score"]:.1f}%' if row["average_score"] is not None else "N/A",
                ]
            )
        if len(project_data) == 1:
            project_data.append(["No submitted assessments", "", "", "", "", "", ""])
        project_table = Table(
            project_data,
            colWidths=[45 * mm, 19 * mm, 19 * mm, 20 * mm, 16 * mm, 16 * mm, 30 * mm],
        )
        project_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([project_table, Spacer(1, 6 * mm)])

    sorted_submissions = sorted(
        filtered_submissions,
        key=lambda row: (str(row.get("candidate_name") or "").casefold(), row.get("id", 0)),
    )
    if not sorted_submissions:
        story.append(Paragraph("No submitted assessments are available for this project.", styles["Normal"]))

    for submission in sorted_submissions:
        candidate_name = escape(str(submission.get("candidate_name") or "Unknown candidate"))
        grading_data = [[Paragraph("Assessment detail", header), Paragraph("Result", header)]]
        for label, value in result_table([submission])[0].items():
            rendered_value = escape(str(value or "-"))
            if label == "Candidate":
                rendered_value = f"<b>{rendered_value}</b>"
            grading_data.append([Paragraph(escape(label), normal), Paragraph(rendered_value, normal)])
        grading_table = Table(grading_data, colWidths=[66 * mm, 104 * mm], repeatRows=1)
        grading_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(
            KeepTogether(
                [
                    Paragraph("Grading Summary", styles["Heading2"]),
                    Paragraph(
                        f"Candidate: <b>{candidate_name}</b> | Assessment #{submission.get('id', 'N/A')}",
                        styles["Normal"],
                    ),
                    Spacer(1, 2 * mm),
                    grading_table,
                    Spacer(1, 4 * mm),
                ]
            )
        )
    document.build(story, canvasmaker=NumberedCanvas)
    return output.getvalue()
