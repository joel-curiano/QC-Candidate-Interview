"""Candidate Schedules page - assign test dates, disciplines, and send invitations."""
from datetime import date

import streamlit as st

import database as db
from email_service import EmailDeliveryError, send_candidate_invitation
from email_validation import validate_email_address
from candidate_roles import candidate_roles_for_discipline
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
        key="schedule_selected_candidate",
    )

    if selected_id:
        candidate = next(c for c in filtered if c["id"] == selected_id)
        st.write(
            f"**Email:** {candidate['email']} | **Current Test Date:** {candidate['test_date']}"
        )

        disciplines = cached_disciplines()
        discipline_options = ["Select discipline"] + disciplines
        current_discipline = candidate.get("scheduled_discipline")
        discipline_key = f"schedule_discipline_{candidate['id']}"
        if discipline_key not in st.session_state:
            st.session_state[discipline_key] = (
                current_discipline if current_discipline in discipline_options else "Select discipline"
            )
        scheduled_discipline = st.selectbox(
            "Candidate Discipline *",
            discipline_options,
            key=discipline_key,
        )
        candidate_role_options = (
            ["Select role", *candidate_roles_for_discipline(scheduled_discipline)]
            if scheduled_discipline != "Select discipline"
            else ["Select role"]
        )
        candidate_role_key = f"schedule_candidate_role_{candidate['id']}"
        if st.session_state.get(candidate_role_key) not in candidate_role_options:
            current_role = candidate.get("candidate_role") or ""
            st.session_state[candidate_role_key] = (
                current_role if current_role in candidate_role_options else "Select role"
            )
        candidate_role = st.selectbox(
            "Candidate Role *",
            candidate_role_options,
            key=candidate_role_key,
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
                or (
                    bool(candidate.get("test_date"))
                    and schedule_date == candidate.get("test_date")
                    and project_assignment == candidate.get("project_assignment")
                    and scheduled_discipline == candidate.get("scheduled_discipline")
                    and candidate_role == candidate.get("candidate_role")
                )
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
                    if candidate_role == "Select role":
                        raise ValueError("Candidate Role is required.")
                    if project_assignment == "Select project assignment":
                        raise ValueError("Project Assignment is required.")
                    db.update_candidate_schedule(
                        user["id"], candidate["id"], schedule_date,
                        project_assignment, scheduled_discipline, candidate_role,
                    )
                    temporary_password = db.generate_password(length=6, alphanumeric_only=True)
                    db.set_candidate_temporary_password(
                        user["id"], candidate["id"], temporary_password
                    )
                    clear_read_caches()
                    st.session_state.candidate_schedule_saved = {
                        "candidate_name": candidate["name"],
                        "username": candidate["username"],
                        "temporary_password": temporary_password,
                        "test_date": schedule_date.strftime("%A, %d %B %Y"),
                        "discipline": scheduled_discipline,
                        "candidate_role": candidate_role,
                        "project_assignment": project_assignment,
                    }
                    st.session_state.candidate_schedule_saved_id = candidate["id"]
                    st.session_state[
                        f"candidate_schedule_temporary_password_{candidate['id']}"
                    ] = temporary_password
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

            if send_schedule:
                try:
                    validate_email_address(candidate['email'], 'Candidate email in Accounts')
                    password_key = f"candidate_schedule_temporary_password_{candidate['id']}"
                    temporary_password = st.session_state.get(password_key)
                    if not temporary_password:
                        temporary_password = db.generate_password(length=6, alphanumeric_only=True)
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
                        candidate.get("candidate_role", ""),
                    )
                    db.mark_invitation_sent(user["id"], candidate["id"])
                    clear_read_caches()
                    st.session_state.candidate_schedule_sent = {
                        "candidate_name": candidate["name"],
                        "email": candidate["email"],
                    }
                    st.session_state.pop("candidate_schedule_saved_id", None)
                    st.session_state.pop(password_key, None)
                    st.rerun()
                except (EmailDeliveryError, OSError, ValueError) as exc:
                    st.error(str(exc))

if saved_schedule:
    with st.container(border=True):
        st.success(f"Schedule saved for {saved_schedule['candidate_name']}.")
        st.write(
            f"{saved_schedule['test_date']} | {saved_schedule['discipline']} | "
            f"{saved_schedule['candidate_role']} | Project: {saved_schedule['project_assignment']}"
        )
        username_column, password_column = st.columns(2)
        with username_column:
            st.caption('Username')
            st.code(saved_schedule['username'], language=None)
        with password_column:
            st.caption('Temporary password')
            st.code(saved_schedule['temporary_password'], language=None)
        st.caption('Use Send Schedule to email these credentials to the candidate.')
if sent_schedule:
    st.success(
        f"Schedule and login credentials sent to {sent_schedule['candidate_name']} "
        f"at {sent_schedule['email']}."
    )
