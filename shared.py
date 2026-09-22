"""Shared helpers, caching, CSS, and session utilities for all CTA Portal pages.

Process flow:
  1. Import this module at the top of every page.
  2. Call require_login() to enforce authentication and return the active user.
  3. Call inject_global_styles() once per page render.
  4. Use cached_* helpers instead of calling database functions directly.
"""

import base64
import json
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import database as db


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
SIDEBAR_WIDTH_PX = 285


# ---------------------------------------------------------------------------
# Global CSS (injected once per page)
# ---------------------------------------------------------------------------
def inject_global_styles() -> None:
    """Inject brand CSS and sidebar sizing into the current page."""
    st.markdown(
        f"""<style>
        [data-testid="stSidebar"] {{
            background-color: #d9dcde;
            width: {SIDEBAR_WIDTH_PX}px !important;
            min-width: {SIDEBAR_WIDTH_PX}px !important;
            max-width: {SIDEBAR_WIDTH_PX}px !important;
        }}
        [data-testid="stSidebar"] [data-testid="stExpander"] {{
            width: 85% !important;
            margin-left: auto;
            margin-right: auto;
        }}
        .cat-theme-icon {{ display: block; width: 128px; height: 128px; object-fit: contain; margin: 0 0 4px 0; }}
        .cat-theme-icon.dark {{ display: none; }}
        [data-testid="stMainBlockContainer"] {{ padding-top: 3rem; }}
        .company-details {{ color: #4B5563; font-size: 0.82rem; line-height: 1.45; margin: 0.1rem 0 1.2rem 0; }}
        .company-details strong {{ color: #b51f2d; }}
        [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{
            position: fixed; top: 72px; right: 24px; width: 380px;
            z-index: 9999; background: #ffffff;
            border: 2px solid #b51f2d; border-radius: 10px;
            box-shadow: 0 4px 14px rgba(20,39,53,0.22);
            padding: 6px 12px; min-height: 82px; overflow: visible;
        }}
        [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) iframe {{
            width: 100% !important; height: 82px !important; min-height: 82px !important; display: block;
        }}
        @media (max-width: 640px) {{
            [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{
                top: 56px; right: 10px; left: 10px; width: auto;
            }}
        }}
        @media (prefers-color-scheme: dark) {{
            .cat-theme-icon.light {{ display: none; }}
            .cat-theme-icon.dark {{ display: block; }}
        }}
        [data-testid="stMarkdownContainer"] h3 {{ color: #b51f2d !important; }}
        .stButton > button, .stDownloadButton > button {{
            background-color: #ffffff; border: 1px solid #b51f2d;
            color: #8f1824; font-weight: 600;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background-color: #fce8eb; border-color: #8f1824; color: #8f1824;
        }}
        .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
            background-color: #b51f2d; border-color: #b51f2d; color: #ffffff;
        }}
        .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
            background-color: #8f1824; border-color: #8f1824; color: #ffffff;
        }}
        .stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
            box-shadow: 0 0 0 3px rgba(181,31,45,0.25); outline: none;
        }}
        .stButton > button:disabled, .stDownloadButton > button:disabled {{
            background-color: #e2e8f0; border-color: #cbd5e1; color: #64748b;
        }}
        .logo-container {{ text-align: left; margin-bottom: 0.5rem; }}
        .logo-container img {{ width: 240px; max-width: 100%; margin-left: 0; }}
        @media (orientation: portrait) {{
            .logo-container img {{ max-width: 70% !important; }}
            h1 {{ font-size: 1.5rem !important; }}
        }}
        [data-testid="stSidebarNav"] ul li:first-child {{ display: none !important; }}
        </style>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Logo / icon helpers
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def cat_icon_data_url(filename: str) -> str:
    """Return a base-64 data-URL for a logo file in the img/ directory."""
    base = Path(__file__).resolve().parent.parent
    path = base / "img" / filename
    if not path.exists():
        path = Path("img") / filename
    if not path.exists():
        return ""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    content_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{content_type};base64,{encoded}"


def render_logo() -> None:
    """Render the C.A.T. logo and company sub-heading."""
    st.markdown(
        f"""<div class="logo-container">
    <img src="{cat_icon_data_url('C.A.T. Logo - Horizontal.jpg')}" alt="C.A.T. Logo">
</div>
<div class="company-details">
    <strong>QUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.</strong><br>
    Ash Shulah, Dammam 34266, Saudi Arabia
</div>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Cached database read helpers (TTL-based)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def cached_disciplines() -> list:
    return db.disciplines()


@st.cache_data(ttl=30, show_spinner=False)
def cached_questions(discipline=None, include_inactive: bool = False) -> list:
    return db.questions(discipline, include_inactive=include_inactive)


@st.cache_data(ttl=30, show_spinner=False)
def cached_assessment_settings(actor_id: int) -> dict:
    return db.assessment_settings(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_projects(actor_id: int) -> list:
    return db.get_projects(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_candidate_accounts(actor_id: int) -> list:
    return db.candidate_accounts(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_submissions(actor_id: int) -> list:
    return db.submissions(actor_id)


@st.cache_data(ttl=600, show_spinner=False)
def cached_has_users() -> bool:
    return db.has_users()


def clear_read_caches() -> None:
    """Invalidate all TTL-based read caches after a write operation."""
    cached_has_users.clear()
    cached_disciplines.clear()
    cached_questions.clear()
    cached_assessment_settings.clear()
    cached_projects.clear()
    cached_candidate_accounts.clear()
    cached_submissions.clear()


# ---------------------------------------------------------------------------
# Session / authentication helpers
# ---------------------------------------------------------------------------
def require_login() -> dict:
    """Enforce login and session freshness. Returns the active user dict.

    Process flow:
      1. Redirect to login (app.py root) if session is absent or invalid.
      2. Refresh the server-side login heartbeat every 60 s.
      3. Enforce maintenance mode for non-Admin users.
    """
    if "user" not in st.session_state or not st.session_state.get("login_token"):
        st.session_state.clear()
        st.switch_page("app.py")
        st.stop()

    user = st.session_state.user
    login_token = st.session_state.login_token
    now = time.time()
    last_refresh = st.session_state.get("last_login_refresh", 0)

    # Refresh login heartbeat every 60 seconds.
    if now - last_refresh > 60:
        refreshed = db.refresh_login(user["id"], login_token)
        if not refreshed:
            st.session_state.clear()
            st.session_state.timeout_message = (
                "You were signed out after 30 minutes of inactivity. Please sign in again."
            )
            st.switch_page("app.py")
            st.stop()
        user = refreshed
        st.session_state.user = user
        st.session_state.last_login_refresh = now

    # Enforce maintenance mode for non-Admin roles.
    if db.maintenance_mode() and user["role"] != "Admin":
        db.release_login(user["id"], login_token)
        st.session_state.clear()
        st.warning(
            "The portal is temporarily unavailable while maintenance is in progress. "
            "Please try again later."
        )
        st.stop()

    return user


def sidebar_nav(user: dict) -> None:
    """Render sidebar user info, change-password expander, and sign-out button."""
    try:
        st.logo("img/Icon/CAT Icon White Background.png", icon_image="img/Icon/CAT-Tab-Icon.png")
    except AttributeError:
        st.sidebar.image("img/Icon/CAT Icon White Background.png", use_container_width=True)
    st.sidebar.write(f"**{user['name']}**")
    st.sidebar.caption(user["role"])

    if user["role"] in ("Admin", "Reviewer"):
        with st.sidebar.expander("Change password"):
            def _generate_new_password():
                generated = db.generate_password()
                st.session_state.change_new_password = generated
                st.session_state.change_confirm_password = generated
                st.session_state.change_generated_password = generated

            with st.form("change_password_form"):
                current_password = st.text_input("Current password", type="password")
                new_password = st.text_input(
                    "New password (at least 6 characters)", type="password", key="change_new_password"
                )
                confirm_password = st.text_input(
                    "Confirm new password", type="password", key="change_confirm_password"
                )
                st.form_submit_button("Generate random password", on_click=_generate_new_password)
                if st.form_submit_button("Change password", type="primary"):
                    try:
                        if new_password != confirm_password:
                            raise ValueError("New passwords do not match.")
                        db.change_password(user["id"], current_password, new_password)
                        db.release_login(user["id"], st.session_state.login_token)
                        st.session_state.clear()
                        st.session_state.password_changed = True
                        st.switch_page("app.py")
                    except ValueError as exc:
                        st.error(str(exc))
            if generated := st.session_state.get("change_generated_password"):
                st.caption("Copy your generated password before saving:")
                st.code(generated, language=None)

    if st.sidebar.button("Sign out"):
        db.release_login(user["id"], st.session_state.login_token)
        st.session_state.clear()
        st.switch_page("app.py")


# ---------------------------------------------------------------------------
# Server-side countdown timer
# ---------------------------------------------------------------------------
def countdown_timer(label: str, deadline: float, key: str) -> None:
    """Render a client-side countdown driven by a server-calculated deadline.

    The deadline (Unix timestamp) is computed server-side, so a browser
    refresh or device switch cannot reset or extend the allowed time.
    """
    remaining = max(0, int(deadline - time.time()))
    components.html(
        f"""
        <div id="timer-{key}" style="font-family:sans-serif;color:#b51f2d;padding:6px 0;
             text-align:center;min-height:70px;box-sizing:border-box">
          <div style="font-size:14px;font-weight:600;line-height:18px;white-space:normal">{label}</div>
          <div id="value-{key}" style="font-size:26px;font-weight:700;line-height:32px;white-space:nowrap"></div>
        </div>
        <script>
        (() => {{
          let seconds = {remaining};
          const value = document.getElementById('value-{key}');
          const render = () => {{
            const m = Math.floor(seconds / 60);
            const s = String(seconds % 60).padStart(2, '0');
            value.textContent = `${{m}}:${{s}}`;
            if (seconds <= 0) value.textContent = 'Time expired';
            seconds = Math.max(0, seconds - 1);
          }};
          render();
          setInterval(render, 1000);
        }})();
        </script>
        """,
        height=82,
    )


# ---------------------------------------------------------------------------
# Result formatting helpers (shared between Review Assessments and PDF export)
# ---------------------------------------------------------------------------
def format_result_datetime(value: str) -> str:
    if not value:
        return ""
    text = str(value).replace("T", " ").replace("Z", "")
    if "." in text:
        text = text.split(".", 1)[0]
    if "+" in text[10:]:
        text = text.split("+", 1)[0]
    if len(text) == 10:
        return f"{text} 00:00"
    return text[:16]


def result_table(rows: list) -> list:
    return [
        {
            "Candidate": r["candidate_name"],
            "Job Title": r.get("designation", ""),
            "Employee No": r.get("employee_no", ""),
            "Discipline": r["discipline"],
            "Project Assignment": r.get("project_assignment", ""),
            "Exam Date": format_result_datetime(r.get("exam_date", "")),
            "Status": r["status"],
            "Multiple Choice Grade": db.category_result(r, "mcq"),
            "Essay Grade": db.category_result(r, "essay"),
            "Oral-Practical Grade": db.category_result(r, "oral_practical"),
            "Reviewer Comments": r.get("reviewer_comments", ""),
            "Graded (UTC)": format_result_datetime(r.get("graded_at", "")),
            "Overall Result": db.result(r),
        }
        for r in rows
    ]

