"""Candidate Schedules page - assign test dates, disciplines, and send invitations."""
from datetime import date

import streamlit as st

import database as db
from email_service import EmailDeliveryError, send_candidate_invitation
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_candidate_accounts,
    cached_disciplines,
    cached_projects,
    clear_read_caches,
)

st.set_page_config(
    page_title="Candidate Schedules - CTA Portal",
    page_icon=":material/calendar_month:",
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
st.subheader("Candidate Schedules")

# Consume one-shot messages written before st.rerun() calls.
saved_schedule = st.session_state.pop("candidate_schedule_saved", None)
sent_schedule = st.session_state.pop("candidate_schedule_sent", None)

candidates = cached_candidate_accounts(user["id"])

# Filter controls - two per row to stay readable on centred/narrow layouts.
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    search_name = st.selectbox(
        "Filter by Name",
        ["All"] + sorted({c["name"] for c in candidates}),
        key="schedule_filter_name",
    )
with row1_col2:
    search_discipline = st.selectbox(
        "Filter by Scheduled Discipline",
        ["All"] + sorted({c["scheduled_discipline"] for c in candidates if c.get("scheduled_discipline")}),
        key="schedule_filter_discipline",
    )
with row2_col1:
    search_iqama = st.selectbox(
        "Filter by Iqama",
        ["All"] + sorted({c["iqama_no"] for c in candidates if c.get("iqama_no")}),
        key="schedule_filter_iqama",
    )
with row2_col2:
    search_completion = st.selectbox(
        "Assessment Completion Status",
        ["All", "Complete", "Incomplete"],
        key="schedule_filter_completion",
    )

# Apply filters in Python (dataset is small - max ~10 candidates).
filtered = candidates
if search_name != "All":
    filtered = [c for c in filtered if c["name"] == search_name]
if search_discipline != "All":
    filtered = [c for c in filtered if c.get("scheduled_discipline") == search_discipline]
if search_iqama != "All":
    filtered = [c for c in filtered if c["iqama_no"] == search_iqama]
if search_completion != "All":
    filtered = [c for c in filtered if c.get("assessment_completion_status") == search_completion]

if not filtered:
    st.info("No candidates found matching the filters.")
else:
    options = {
        c["id"]: (
            f"{c['name']} - {c.get('scheduled_discipline', '')} "
            f"- {c['iqama_no']} - {c.get('assessment_completion_status', 'Incomplete')}"
        )
        for c in filtered
    }
    selected_id = st.selectbox(
        "Select Candidate",
        options=list(options.keys()),
        format_func=lambda x: options[x],
    )

    if selected_id:
        candidate = next(c for c in filtered if c["id"] == selected_id)
        st.write(
            f"**Email:** {candidate['email']} | **Current Test Date:** {candidate['test_date']}"
        )

        with st.form(f"schedule_{candidate['id']}"):
            current_test_date = candidate["test_date"]
            schedule_date = st.date_input(
                "Test date schedule *",
                value=current_test_date,
                min_value=(
                    min(current_test_date, date.today()) if current_test_date else date.today()
                ),
            )
            disciplines = cached_disciplines()
            discipline_options = ["Select discipline"] + disciplines
            current_discipline = candidate.get("scheduled_discipline")
            scheduled_discipline = st.selectbox(
                "Candidate Discipline *",
                discipline_options,
                index=(
                    discipline_options.index(current_discipline)
                    if current_discipline in discipline_options
                    else 0
                ),
            )
            projects = cached_projects(user["id"])
            project_options = ["Select project assignment", "Unassigned"] + [
                p for p in projects if p != "Unassigned"
            ]
            current_project = candidate.get("project_assignment")
            project_assignment = st.selectbox(
                "Project Assignment *",
                project_options,
                index=(
                    project_options.index(current_project)
                    if current_project in project_options
                    else 0
                ),
                help="Use Unassigned for new applicants taking the CTA before a project is assigned.",
            )
            save_col, send_col = st.columns(2)
            with save_col:
                save_schedule = st.form_submit_button("Save Schedule", type="primary")

            # Send button is only enabled once the schedule has been saved.
            saved_for_candidate = (
                st.session_state.get("candidate_schedule_saved_id") == candidate["id"]
                or bool(candidate.get("test_date"))
            )
            with send_col:
                send_schedule = st.form_submit_button(
                    "Send Schedule", disabled=not saved_for_candidate
                )

            if save_schedule:
                try:
                    if not schedule_date:
                        raise ValueError("Candidate test date is required.")
                    if schedule_date < date.today():
                        raise ValueError("Test date must be today or a future date.")
                    if scheduled_discipline == "Select discipline":
                        raise ValueError("Candidate Discipline is required.")
                    if project_assignment == "Select project assignment":
                        raise ValueError("Project Assignment is required.")
                    db.update_candidate_schedule(
                        user["id"], candidate["id"], schedule_date,
                        project_assignment, scheduled_discipline,
                    )
                    clear_read_caches()
                    st.session_state.candidate_schedule_saved = {
                        "candidate_name": candidate["name"],
                        "test_date": schedule_date.strftime("%A, %d %B %Y"),
                        "discipline": scheduled_discipline,
                        "project_assignment": project_assignment,
                    }
                    st.session_state.candidate_schedule_saved_id = candidate["id"]
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

            if send_schedule:
                try:
                    temporary_password = db.generate_password()
                    db.set_candidate_temporary_password(
                        user["id"], candidate["id"], temporary_password
                    )
                    send_candidate_invitation(
                        candidate["email"],
                        candidate["name"],
                        candidate["username"],
                        temporary_password,
                        candidate["test_date"],
                        candidate.get("scheduled_discipline") or candidate["discipline"],
                    )
                    db.mark_invitation_sent(user["id"], candidate["id"])
                    clear_read_caches()
                    st.session_state.candidate_schedule_sent = {
                        "candidate_name": candidate["name"],
                        "email": candidate["email"],
                    }
                    st.session_state.pop("candidate_schedule_saved_id", None)
                    st.rerun()
                except (EmailDeliveryError, OSError, ValueError) as exc:
                    st.error(str(exc))

if saved_schedule:
    st.success(
        f"Schedule saved for {saved_schedule['candidate_name']}: "
        f"{saved_schedule['test_date']} | {saved_schedule['discipline']} | "
        f"Project: {saved_schedule['project_assignment']}"
    )
if sent_schedule:
    st.success(
        f"Schedule and login credentials sent to {sent_schedule['candidate_name']} "
        f"at {sent_schedule['email']}."
    )

