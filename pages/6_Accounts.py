"""Accounts page - manage candidate and staff accounts."""
import streamlit as st
import re
import secrets

import database as db
from email_service import EmailDeliveryError, send_reviewer_credentials
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_disciplines,
    cached_candidate_accounts,
    cached_projects,
    clear_read_caches,
)

st.set_page_config(
    page_title="Accounts - CTA Portal",
    page_icon=":material/manage_accounts:",
    layout="centered",
)
inject_global_styles()

user = require_login()
if user["role"] != "Admin":
    st.error("Access denied.")
    st.stop()

sidebar_nav(user)
render_logo()
st.title("Competency Technical Assessment (CTA) Portal")
st.subheader("Accounts")

projects = cached_projects(user["id"])

# ---------------------------------------------------------------------------
# Manage Candidate Accounts section
# ---------------------------------------------------------------------------
with st.expander("Manage Candidate Accounts"):
    candidates = cached_candidate_accounts(user["id"])
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_name = st.selectbox(
            "Filter by Name",
            ["All"] + sorted({c["name"] for c in candidates}),
            key="accounts_filter_name",
        )
    with col2:
        filter_discipline = st.selectbox(
            "Filter by Discipline",
            ["All"] + sorted({
                c.get("scheduled_discipline") or c.get("discipline", "")
                for c in candidates
                if c.get("scheduled_discipline") or c.get("discipline")
            }),
            key="accounts_filter_discipline",
        )
    with col3:
        filter_iqama = st.selectbox(
            "Filter by Iqama",
            ["All"] + sorted({c["iqama_no"] for c in candidates if c.get("iqama_no")}),
            key="accounts_filter_iqama",
        )

    filtered = candidates
    if filter_name != "All":
        filtered = [c for c in filtered if c["name"] == filter_name]
    if filter_discipline != "All":
        filtered = [
            c for c in filtered
            if (c.get("scheduled_discipline") or c.get("discipline", "")) == filter_discipline
        ]
    if filter_iqama != "All":
        filtered = [c for c in filtered if c["iqama_no"] == filter_iqama]

    if not filtered:
        st.info("No candidate accounts match the filters.")
    else:
        options = {c["id"]: f"{c['name']} - {c['iqama_no']}" for c in filtered}
        selected_id = st.selectbox(
            "Select Candidate Account",
            list(options),
            format_func=lambda v: options[v],
            key="candidate_account_selection",
        )
        candidate = next(c for c in filtered if c["id"] == selected_id)
        with st.form("edit_candidate_account"):
            name = st.text_input("Full name *", value=candidate.get("name", ""))
            email = st.text_input("Email *", value=candidate.get("email", ""))
            iqama_no = st.text_input("Iqama No *", value=candidate.get("iqama_no", ""))
            employee_no = st.text_input("Employee No", value=candidate.get("employee_no", ""))
            mobile_no = st.text_input("Mobile No", value=candidate.get("mobile_no", ""))
            if st.form_submit_button("Save Candidate Details", type="primary"):
                try:
                    if not all(v.strip() for v in (name, email, iqama_no)):
                        raise ValueError("Name, email, and Iqama No are required.")
                    db.update_candidate_details(
                        user["id"], selected_id, name, email, iqama_no, employee_no, mobile_no
                    )
                    clear_read_caches()
                    st.success("Candidate details updated successfully.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

st.divider()

# ---------------------------------------------------------------------------
# Create staff account
# ---------------------------------------------------------------------------
def account_form_staff(key, actor, allowed_roles):
    """Render the staff account creation form.

    Usage: account_form_staff('staff', actor=user['id'], allowed_roles=['Reviewer', 'Admin'])
    """
    password_key = f"{key}_password"
    confirm_key = f"{key}_confirm_password"
    generated_key = f"{key}_generated_password"
    field_reset = st.session_state.get(f"{key}_reset", 0)
    name_key = f"{key}_full_name_{field_reset}"
    username_key = f"{key}_username_{field_reset}"
    username_taken_key = f"{key}_username_taken"

    def suggest_username():
        full_name = st.session_state.get(name_key, "")
        base_username = re.sub(r"[^a-z0-9]+", ".", full_name.lower()).strip(".")
        if not base_username:
            return
        suggestion = base_username
        if db.username_exists(suggestion):
            while True:
                suggestion = f"{base_username}{secrets.randbelow(1000):03d}"
                if not db.username_exists(suggestion):
                    break
        st.session_state[username_key] = suggestion
        st.session_state[username_taken_key] = False

    def check_username_availability():
        username = st.session_state.get(username_key, "").strip()
        st.session_state[username_taken_key] = bool(username) and db.username_exists(username)

    def generate_account_password():
        generated = db.generate_password()
        st.session_state[password_key] = generated
        st.session_state[confirm_key] = generated
        st.session_state[generated_key] = generated

    name = st.text_input("Full name *", key=name_key, on_change=suggest_username)
    username = st.text_input(
        "Username *", key=username_key, on_change=check_username_availability
    )
    if st.session_state.get(username_taken_key):
        st.warning("This username is already taken. Please choose another username.")

    form_key = f"{key}_{field_reset}"
    with st.form(form_key):
        account_email = st.text_input("Email *")
        password = st.text_input(
            "Password (at least 6 characters)", type="password", key=password_key
        )
        confirm = st.text_input("Confirm password", type="password", key=confirm_key)
        role = st.selectbox("Role", allowed_roles)
        reviewer_disciplines = ["All Disciplines"]
        if role == "Reviewer":
            reviewer_disciplines = st.multiselect(
                "Reviewer disciplines",
                ["All Disciplines"] + cached_disciplines(),
                default=["All Disciplines"],
                help="Select All Disciplines to allow this Reviewer to assess all disciplines.",
            )
        st.form_submit_button("Generate random password", on_click=generate_account_password)
        if st.form_submit_button("Create account", type="primary"):
            try:
                if password != confirm:
                    raise ValueError("Passwords do not match.")
                if db.username_exists(username):
                    raise ValueError("This username is already taken.")
                if role == "Reviewer" and not account_email.strip():
                    raise ValueError("Reviewer email is required.")
                candidate_id = db.create_user(
                    username, name, password, role, actor, False, email=account_email,
                )
                if role == "Reviewer":
                    db.update_reviewer_disciplines(actor, candidate_id, reviewer_disciplines)
                    try:
                        send_reviewer_credentials(
                            account_email.strip().lower(), name.strip(),
                            username.strip().lower(), password,
                        )
                        st.session_state.pop(generated_key, None)
                        clear_read_caches()
                        st.success("Reviewer account created and login credentials emailed.")
                    except (EmailDeliveryError, OSError, ValueError) as exc:
                        st.warning(
                            f"Account created, but the credentials email could not be sent: {exc}"
                        )
                else:
                    st.session_state.pop(generated_key, None)
                    clear_read_caches()
                    st.success("Account created.")
            except ValueError as exc:
                st.error(str(exc))

    if generated_key in st.session_state:
        st.caption("Copy this generated password and give it securely to the account owner:")
        st.code(st.session_state[generated_key], language=None)


st.subheader("Create account")
account_form_staff("staff", actor=user["id"], allowed_roles=["Reviewer", "Admin"])

st.divider()

# ---------------------------------------------------------------------------
# Existing staff accounts
# ---------------------------------------------------------------------------
st.subheader("Existing accounts")
for staff in db.staff_accounts(user["id"]):
    with st.expander(f"{staff['name']} ({staff['username']}) - {staff['role']}"):
        st.write(f"Email: {staff['email']}")

        if staff["role"] == "Reviewer":
            with st.form(f"update_reviewer_email_{staff['id']}"):
                reviewer_email = st.text_input("Reviewer email", value=staff.get("email", ""))
                if st.form_submit_button("Save Reviewer email"):
                    try:
                        db.update_reviewer_email(user["id"], staff["id"], reviewer_email)
                        st.success("Reviewer email saved.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            with st.form(f"change_reviewer_password_{staff['id']}"):
                new_reviewer_password = st.text_input(
                    "New password (at least 6 characters)", type="password"
                )
                confirm_reviewer_password = st.text_input("Confirm new password", type="password")
                if st.form_submit_button("Change Reviewer password"):
                    try:
                        if new_reviewer_password != confirm_reviewer_password:
                            raise ValueError("Passwords do not match.")
                        db.set_reviewer_temporary_password(
                            user["id"], staff["id"], new_reviewer_password
                        )
                        st.session_state[f"reviewer_password_{staff['id']}"] = new_reviewer_password
                        st.success("Reviewer password changed. Send the credentials when ready.")
                    except ValueError as exc:
                        st.error(str(exc))

            if st.button("Send Reviewer Credentials", key=f"email_reviewer_{staff['id']}"):
                try:
                    if not staff["email"]:
                        raise ValueError("This Reviewer does not have an email address.")
                    temporary_password = st.session_state.get(f"reviewer_password_{staff['id']}")
                    if not temporary_password:
                        raise ValueError(
                            "Change the Reviewer password first, then send the credentials."
                        )
                    send_reviewer_credentials(
                        staff["email"], staff["name"], staff["username"], temporary_password
                    )
                    st.session_state.pop(f"reviewer_password_{staff['id']}", None)
                    st.success("Reviewer login credentials emailed.")
                except (EmailDeliveryError, OSError, ValueError) as exc:
                    st.error(str(exc))

            with st.form(f"assign_proj_{staff['id']}"):
                assigned = st.multiselect(
                    "Assigned Projects list box",
                    projects,
                    default=staff.get("assigned_projects", []),
                )
                if st.form_submit_button("Save Assignments"):
                    try:
                        db.update_staff_projects(user["id"], staff["id"], assigned)
                        st.success("Assignments saved.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            discipline_options = ["All Disciplines"] + cached_disciplines()
            current_disciplines = [
                d for d in staff.get("assigned_disciplines", ["All Disciplines"])
                if d in discipline_options
            ] or ["All Disciplines"]
            with st.form(f"assign_disciplines_{staff['id']}"):
                assigned_disciplines = st.multiselect(
                    "Reviewer disciplines",
                    discipline_options,
                    default=current_disciplines,
                    help="All Disciplines gives this Reviewer access to every discipline.",
                )
                if st.form_submit_button("Save Reviewer Disciplines"):
                    try:
                        db.update_reviewer_disciplines(
                            user["id"], staff["id"], assigned_disciplines
                        )
                        st.success("Reviewer disciplines saved.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

        if staff["id"] != user["id"]:
            if st.button("Delete Account", key=f"del_staff_{staff['id']}", type="primary"):
                try:
                    db.delete_user(user["id"], staff["id"])
                    clear_read_caches()
                    st.success("Staff account deleted.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

