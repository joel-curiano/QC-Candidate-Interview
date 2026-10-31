"""Assessment analytics page for Admins and Reviewers."""
import re

import streamlit as st

from assessment_analytics import analytics_pdf_bytes, summarize_assessments
from shared import (
    cached_submissions,
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
)

st.set_page_config(
    page_title="Assessment Analytics - CTA Portal",
    page_icon=":material/analytics:",
    layout="wide",
)
inject_global_styles()

user = require_login()
if user["role"] not in ("Admin", "Reviewer"):
    st.error("Access denied.")
    st.stop()

sidebar_nav(user)
render_logo()
st.title("Competency Technical Assessment (CTA) Portal")
st.subheader("Assessment Analytics")
st.caption(
    "Counts are submitted assessments, not unique candidates. Project grouping uses each "
    "candidate's current project assignment. Pass and fail percentages include graded "
    "assessments only; Pending Review assessments are shown separately."
)

submissions = cached_submissions(user["id"])
summary = summarize_assessments(submissions)
totals = summary["totals"]
project_rows = summary["projects"]
project_options = ["All projects", *(row["project"] for row in project_rows)]
selected_project = st.selectbox("Project", project_options)

if selected_project == "All projects":
    selected_summary = totals
    visible_project_rows = project_rows
else:
    selected_summary = next(row for row in project_rows if row["project"] == selected_project)
    visible_project_rows = [selected_summary]

first_row = st.columns(3)
first_row[0].metric("Total assessments", selected_summary["total"])
first_row[1].metric("Pass", selected_summary["passed"])
first_row[2].metric("Fail", selected_summary["failed"])

second_row = st.columns(4)
second_row[0].metric("Graded", selected_summary["graded"])
second_row[1].metric("Pending review", selected_summary["pending"])
second_row[2].metric(
    "Pass rate",
    (
        f'{selected_summary["pass_rate"]:.1f}%'
        if selected_summary["pass_rate"] is not None
        else "N/A"
    ),
    help="Passed assessments divided by all graded assessments.",
)
second_row[3].metric(
    "Fail rate",
    (
        f'{selected_summary["fail_rate"]:.1f}%'
        if selected_summary["fail_rate"] is not None
        else "N/A"
    ),
    help="Failed assessments divided by all graded assessments.",
)

pdf_project_name = re.sub(r"[^A-Za-z0-9]+", "_", selected_project).strip("_").lower()
st.download_button(
    "Download Analytics PDF",
    data=analytics_pdf_bytes(submissions, selected_project),
    file_name=f"cta_assessment_analytics_{pdf_project_name or 'all_projects'}.pdf",
    mime="application/pdf",
)

st.markdown(
    "#### Results by project"
    if selected_project == "All projects"
    else f"#### Results for {selected_project}"
)
if not visible_project_rows:
    st.info("No submitted assessments are available to analyze.")
else:
    chart_data = [
        {
            "Project": row["project"],
            "Pass": row["passed"],
            "Fail": row["failed"],
            "Pending Review": row["pending"],
        }
        for row in visible_project_rows
    ]
    st.bar_chart(
        chart_data,
        x="Project",
        y=["Pass", "Fail", "Pending Review"],
        color=["#16A34A", "#DC2626", "#F97316"],
    )

    table_rows = [
        {
            "Project": row["project"],
            "Total assessments": row["total"],
            "Graded": row["graded"],
            "Pending review": row["pending"],
            "Pass": row["passed"],
            "Fail": row["failed"],
            "Pass rate": f'{row["pass_rate"]:.1f}%' if row["pass_rate"] is not None else "N/A",
            "Fail rate": f'{row["fail_rate"]:.1f}%' if row["fail_rate"] is not None else "N/A",
            "Average grade": (
                f'{row["average_score"]:.1f}%'
                if row["average_score"] is not None
                else "N/A"
            ),
        }
        for row in visible_project_rows
    ]
    if selected_project == "All projects":
        table_rows.append(
            {
                "Project": "All projects",
                "Total assessments": totals["total"],
                "Graded": totals["graded"],
                "Pending review": totals["pending"],
                "Pass": totals["passed"],
                "Fail": totals["failed"],
                "Pass rate": f'{totals["pass_rate"]:.1f}%' if totals["pass_rate"] is not None else "N/A",
                "Fail rate": f'{totals["fail_rate"]:.1f}%' if totals["fail_rate"] is not None else "N/A",
                "Average grade": (
                    f'{totals["average_score"]:.1f}%'
                    if totals["average_score"] is not None
                    else "N/A"
                ),
            }
        )
    st.dataframe(table_rows, hide_index=True, use_container_width=True)
