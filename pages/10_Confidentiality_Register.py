"""Admin page to view confidentiality acceptances."""

import streamlit as st
import pandas as pd
import database as db
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
)

st.set_page_config(
    page_title="Confidentiality Register - CTA Portal",
    page_icon=":material/policy:",
    layout="wide",
)
inject_global_styles()

user = require_login()
if user["role"] != "Admin":
    st.error("Access denied. This page is for Administrators only.")
    st.stop()

sidebar_nav(user)
render_logo()
st.title("Confidentiality Acceptance Register")

acceptances = db.fetch_confidentiality_acceptances()

if not acceptances:
    st.info("No confidentiality acceptances recorded yet.")
    st.stop()

# Build dataframe
df = pd.DataFrame(acceptances)
df["acceptance_time"] = pd.to_datetime(df["acceptance_time"])
df["acceptance_date"] = df["acceptance_time"].dt.date

col1, col2, col3 = st.columns(3)
with col1:
    role_filter = st.multiselect("Filter by Role", options=df["role_at_acceptance"].unique())
with col2:
    date_filter = st.date_input("Filter by Date", value=None)
with col3:
    user_filter = st.text_input("Filter by Username/Name")

filtered_df = df.copy()

if role_filter:
    filtered_df = filtered_df[filtered_df["role_at_acceptance"].isin(role_filter)]

if date_filter:
    if isinstance(date_filter, tuple) and len(date_filter) == 2:
        start_date, end_date = date_filter
        filtered_df = filtered_df[(filtered_df["acceptance_date"] >= start_date) & (filtered_df["acceptance_date"] <= end_date)]
    elif isinstance(date_filter, tuple) and len(date_filter) == 1:
        filtered_df = filtered_df[filtered_df["acceptance_date"] == date_filter[0]]
    elif not isinstance(date_filter, tuple):
         filtered_df = filtered_df[filtered_df["acceptance_date"] == date_filter]

if user_filter:
    user_filter_lower = user_filter.lower()
    filtered_df = filtered_df[
        filtered_df["username"].str.lower().str.contains(user_filter_lower) |
        filtered_df["name"].str.lower().str.contains(user_filter_lower)
    ]

st.dataframe(
    filtered_df[["username", "name", "role_at_acceptance", "agreement_version", "acceptance_time"]].sort_values("acceptance_time", ascending=False),
    width="stretch",
    hide_index=True,
    column_config={
        "username": "Username",
        "name": "Name",
        "role_at_acceptance": "Role at Acceptance",
        "agreement_version": "Agreement Version",
        "acceptance_time": st.column_config.DatetimeColumn("Acceptance Time", format="YYYY-MM-DD HH:mm:ss")
    }
)
