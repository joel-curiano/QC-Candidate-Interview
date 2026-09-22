"""Create Candidate Account page."""
import streamlit as st
import re
import secrets

import database as db
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_disciplines,
    cached_candidate_accounts,
    clear_read_caches,
)
from email_service import EmailDeliveryError, send_reviewer_credentials

st.set_page_config(
    page_title="Create Candidate Account - CTA Portal",
    page_icon=":material/person_add:",
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


def account_form(key, bootstrap=False, actor=None, allowed_roles=None):
    """Render the account creation form.

    Usage: account_form('candidate_account', actor=user['id'], allowed_roles=['Candidate'])
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

    saved_message = st.session_state.pop(f"{key}_saved_message", None)
    name = st.text_input("Full name *", key=name_key, on_change=suggest_username)
    username = st.text_input("Username *", key=username_key, on_change=check_username_availability)
    if st.session_state.get(username_taken_key):
        st.warning("This username is already taken. Please choose another username.")

    form_key = f"{key}_{field_reset}"
    with st.form(form_key):
        is_candidate = allowed_roles == ["Candidate"]
        account_email = (
            st.text_input("Email *")
            if is_candidate or actor is not None or bootstrap
            else ""
        )
        iqama_no = employee_no = mobile_no = ""
        if is_candidate:
            iqama_no = st.text_input("Iqama No *")
            employee_no = st.text_input("Employee No")
            mobile_no = st.text_input("Mobile No")

        if is_candidate:
            password = confirm = db.generate_password()
            st.info("Login credentials will be generated and emailed after the assessment is scheduled.")
        else:
            password = st.text_input(
                "Password (at least 6 characters)", type="password", key=password_key
            )
            confirm = st.text_input("Confirm password", type="password", key=confirm_key)

        role = (
            st.selectbox("Role", allowed_roles or ["Candidate", "Reviewer", "Admin"])
            if actor
            else "Candidate"
        )
        reviewer_disciplines = ["All Disciplines"]
        if role == "Reviewer":
            reviewer_disciplines = st.multiselect(
                "Reviewer disciplines",
                ["All Disciplines"] + cached_disciplines(),
                default=["All Disciplines"],
                help="Select All Disciplines to allow this Reviewer to assess candidates from every discipline.",
            )
        if not is_candidate:
            st.form_submit_button("Generate random password", on_click=generate_account_password)

        if st.form_submit_button("Create account", type="primary"):
            try:
                if password != confirm:
                    raise ValueError("Passwords do not match.")
                if is_candidate and not all(
                    v.strip() for v in (name, username, account_email, iqama_no)
                ):
                    raise ValueError(
                        "Name, username, email, and Iqama No are required for Candidate accounts."
                    )
                if db.username_exists(username):
                    raise ValueError("This username is already taken. Please choose another username.")
                if role == "Reviewer" and not account_email.strip():
                    raise ValueError("Reviewer email is required so login credentials can be sent.")

                candidate_id = db.create_user(
                    username, name, password, role, actor, bootstrap,
                    email=account_email, test_date=None,
                    discipline="", iqama_no=iqama_no,
                    employee_no=employee_no, mobile_no=mobile_no,
                )
                if role == "Reviewer":
                    db.update_reviewer_disciplines(actor, candidate_id, reviewer_disciplines)
                    try:
                        send_reviewer_credentials(
                            account_email.strip().lower(),
                            name.strip(),
                            username.strip().lower(),
                            password,
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
                    if is_candidate:
                        st.session_state[f"{key}_saved_message"] = "Candidate account saved successfully."
                        st.session_state.pop(username_taken_key, None)
                        st.session_state[f"{key}_reset"] = field_reset + 1
                        st.rerun()
                    else:
                        st.success("Account created.")
                if bootstrap:
                    clear_read_caches()
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    if saved_message:
        st.success(saved_message)
    if not is_candidate and generated_key in st.session_state:
        st.caption("Copy this generated password and give it securely to the account owner:")
        st.code(st.session_state[generated_key], language=None)


st.subheader("Create a candidate account")
account_form("candidate_account", actor=user["id"], allowed_roles=["Candidate"])

