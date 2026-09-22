"""Maintenance page - enable/disable portal maintenance mode (Admin only)."""
import streamlit as st

import database as db
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
)

st.set_page_config(
    page_title="Maintenance - CTA Portal",
    page_icon=":material/build:",
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
st.subheader("Maintenance Mode")

maintenance_enabled = db.maintenance_mode()
st.warning(
    "When enabled, Candidates and Reviewers cannot sign in or use the portal. "
    "Administrators remain able to access this page and turn maintenance mode off."
)
with st.form("maintenance_mode"):
    enable_maintenance = st.checkbox(
        "Make the portal unavailable to Candidates and Reviewers",
        value=maintenance_enabled,
    )
    if st.form_submit_button("Save Maintenance Mode", type="primary"):
        db.set_maintenance_mode(user["id"], enable_maintenance)
        st.success(
            "Maintenance mode enabled." if enable_maintenance else "Maintenance mode disabled."
        )
        st.rerun()

