"""Assessment Settings page - question counts, point rubrics, and individual assessment deletion."""
import streamlit as st

import database as db
from email_service import EmailDeliveryError, send_test_email
from question_types import QUESTION_TYPES
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_assessment_settings,
    cached_submissions,
    clear_read_caches,
)

st.set_page_config(
    page_title="Assessment Settings - CTA Portal",
    page_icon=":material/settings:",
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
st.subheader("Assessment Settings")
st.caption(
    "Set question counts and the maximum points awarded per question type. "
    "Changes apply to new assessments."
)

current = cached_assessment_settings(user["id"])

with st.form("assessment_settings"):
    counts = {
        kind: st.number_input(label, min_value=1, max_value=100, value=current[kind], step=1)
        for kind, label in {
            "mcq": "Multiple Choice Questions",
            "essay": "Essay Questions",
            "oral_practical": "Oral-Practical Questions",
        }.items()
    }
    points = {
        kind: st.number_input(
            f"{label} maximum points per question",
            min_value=1.0, max_value=10.0, value=float(current[f"{kind}_points"]), step=1.0,
        )
        for kind, label in {
            "mcq": "Multiple Choice",
            "essay": "Essay",
            "oral_practical": "Oral-Practical",
        }.items()
    }
    if st.form_submit_button("Save Assessment Settings", type="primary"):
        try:
            db.update_assessment_settings(
                user["id"],
                {
                    **{kind: int(v) for kind, v in counts.items()},
                    **{f"{kind}_points": float(v) for kind, v in points.items()},
                },
            )
            clear_read_caches()
            st.success("Assessment Settings saved.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

# Admin-only: delete individual assessment and test email delivery.
if user["role"] == "Admin":
    st.divider()
    st.subheader("Delete Individual Assessment")
    assessments = db.submissions(user["id"])
    if assessments:
        assessment_options = {
            r["id"]: f"#{r['id']} · {r['candidate_name']} · {r['discipline']} · {r['status']}"
            for r in assessments
        }
        delete_id = st.selectbox(
            "Assessment to delete",
            list(assessment_options),
            format_func=lambda v: assessment_options[v],
            key="delete_assessment_id",
        )
        confirm_delete = st.checkbox(
            "I understand this permanently deletes the selected assessment and its answers.",
            key="confirm_delete_assessment",
        )
        if st.button(
            "Delete Selected Assessment", type="secondary", disabled=not confirm_delete
        ):
            try:
                db.delete_assessment(user["id"], delete_id)
                clear_read_caches()
                st.success("Assessment deleted permanently.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        st.info("No assessments are available to delete.")

    st.divider()

    # Test email delivery expander.
    with st.expander("Test email delivery"):
        st.caption(
            "Send a test message to confirm SMTP settings before inviting candidates or reviewers."
        )
        test_email_addr = st.text_input(
            "Admin email address", value=user.get("email", ""), key="admin_test_email"
        )
        if st.button("Send test email", type="primary"):
            recipient = test_email_addr.strip().lower()
            if not recipient:
                st.error("Enter an email address for the test message.")
            elif hasattr(st, "dialog"):
                @st.dialog("Email delivery status")
                def _send_test_email_dialog():
                    status = st.status("Sending test email...", expanded=True)
                    try:
                        send_test_email(recipient, user.get("name") or "Administrator")
                        status.update(label="Test email sent successfully", state="complete", expanded=True)
                        st.success(f"Test email delivered to {recipient}.")
                    except (EmailDeliveryError, OSError, ValueError) as exc:
                        status.update(label="Test email failed", state="error", expanded=True)
                        st.error(str(exc))
                    if st.button("Close", key="close_test_email_status"):
                        st.rerun()
                _send_test_email_dialog()
            else:
                with st.status("Sending test email..."):
                    try:
                        send_test_email(recipient, user.get("name") or "Administrator")
                        st.success(f"Test email sent to {recipient}.")
                    except (EmailDeliveryError, OSError, ValueError) as exc:
                        st.error(str(exc))

