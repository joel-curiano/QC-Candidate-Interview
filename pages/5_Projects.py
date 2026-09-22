"""Projects page - add, list, and delete named project assignments."""
import streamlit as st

import database as db
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_projects,
    clear_read_caches,
)

st.set_page_config(
    page_title="Projects - CTA Portal",
    page_icon=":material/folder:",
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
st.subheader("Projects")

projects = cached_projects(user["id"])

with st.form("add_project_form"):
    new_project = st.text_input("Project entry input box")
    if st.form_submit_button("Add Project"):
        try:
            db.add_project(user["id"], new_project)
            clear_read_caches()
            st.success("Project added.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

st.write("Projects List box:")
for p in projects:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(p)
    with col2:
        if st.button("Delete", key=f"del_proj_{p}"):
            db.delete_project(user["id"], p)
            clear_read_caches()
            st.rerun()

st.divider()

