"""Run with: streamlit run app.py

Entry point for the CTA Portal.

Process flow:
  1. Configure the page and inject global CSS once (cached).
  2. On first run, initialise the database schema (idempotent).
  3. If no users exist, render the bootstrap Admin setup form and stop.
  4. If the user is not signed in, render the login form and stop.
  5. Redirect Admin/Reviewer users to the first page in the pages/ directory.
  6. Candidate users see the assessment runner inline on this page.

Server-side timer:
  The MCQ and Essay deadlines are Unix timestamps stored in the Supabase
  assessment draft (JSON payload).  On browser refresh or device switch the
  draft is restored and the original deadlines are reused, so no extra time
  is granted.  The client-side countdown is purely cosmetic; it is
  re-seeded from the server-calculated remaining seconds on every Streamlit
  rerun.
"""
import base64
import json
import secrets
import time
from datetime import date
from pathlib import Path

from PIL import Image as PILImage
import streamlit as st
import streamlit.components.v1 as components

import database as db
from question_types import QUESTION_TYPES, REVIEWER_SCORED_TYPES
from email_service import EmailDeliveryError, send_reviewer_credentials
from shared import (
    cached_disciplines,
    cached_has_users,
    cached_questions,
    cached_assessment_settings,
    clear_read_caches,
    inject_global_styles,
    render_logo,
    countdown_timer,
)
import re


# ---------------------------------------------------------------------------
# Tab icon - cached to avoid re-reading the file on every rerun
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _load_tab_icon():
    base_dir = Path(__file__).resolve().parent
    icon_png_path = base_dir / "img" / "Icon" / "CAT-Tab-Icon.png"
    static_favicon_path = base_dir / "static" / "favicon.png"

    if icon_png_path.exists():
        try:
            return PILImage.open(icon_png_path)
        except Exception:
            pass

    src_white = base_dir / "img" / "Icon" / "CAT Icon White Background.png"
    if src_white.exists():
        try:
            from PIL import ImageDraw

            src = PILImage.open(src_white).convert("RGBA")
            alpha = src.split()[3]
            bbox = alpha.getbbox()
            cropped = src.crop(bbox) if bbox else src
            size = 512
            badge = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(badge)
            margin, radius, border_w = 20, 112, 14
            draw.rounded_rectangle(
                [margin, margin, size - margin, size - margin],
                radius=radius,
                fill=(255, 255, 255, 255),
                outline=(181, 31, 45, 255),
                width=border_w,
            )
            inner_pad = 56
            max_w, max_h = size - 2 * inner_pad, size - 2 * inner_pad
            w, h = cropped.size
            scale = min(max_w / w, max_h / h)
            cat_resized = cropped.resize((int(w * scale), int(h * scale)), PILImage.Resampling.LANCZOS)
            pos_x = (size - cat_resized.width) // 2
            pos_y = (size - cat_resized.height) // 2
            badge.paste(cat_resized, (pos_x, pos_y), cat_resized)
            icon_png_path.parent.mkdir(parents=True, exist_ok=True)
            static_favicon_path.parent.mkdir(parents=True, exist_ok=True)
            badge.save(icon_png_path, format="PNG")
            badge.save(static_favicon_path, format="PNG")
            return badge
        except Exception:
            pass

    return "🐱"


CAT_TAB_ICON = _load_tab_icon()

st.set_page_config(
    page_title="Competency Technical Assessment (CTA) Portal",
    page_icon=CAT_TAB_ICON,
    layout="centered",
)
st.markdown(
    '<link rel="icon" type="image/png" href="/app/static/favicon.png">'
    '<link rel="shortcut icon" type="image/png" href="/app/static/favicon.png">'
    '<link rel="apple-touch-icon" href="/app/static/favicon.png">',
    unsafe_allow_html=True,
)
inject_global_styles()


# ---------------------------------------------------------------------------
# Database initialisation (runs once per Streamlit process lifetime)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def initialize_database(schema_version):
    db.init_db()
    db.invalidate_all_logins()
    return True


try:
    with st.spinner("Loading Competency Technical Assessment (CTA) Portal..."):
        initialize_database(4)
except db.DatabaseError as exc:
    st.error(str(exc))
    st.stop()


# ---------------------------------------------------------------------------
# Assessment constants
# ---------------------------------------------------------------------------
MCQ_TIME_LIMIT_SECONDS = 40 * 60
ESSAY_TIME_LIMIT_SECONDS = 6 * 60

ASSESSMENT_DRAFT_KEYS = (
    "assessment_discipline",
    "attempt_token",
    "candidate_details",
    "assessment_mcq_ids",
    "assessment_essay_ids",
    "assessment_reviewer_ids",
    "assessment_mcq_options",
    "assessment_mcq_deadline",
    "assessment_essay_started_at",
    "assessment_essay_index",
    "assessment_counts",
    "assessment_phase",
    "assessment_responses",
)


# ---------------------------------------------------------------------------
# Assessment draft helpers
# ---------------------------------------------------------------------------
def save_current_assessment_draft(candidate_id: int) -> None:
    """Persist the current assessment state to the database draft."""
    payload = {
        key: st.session_state[key]
        for key in ASSESSMENT_DRAFT_KEYS
        if key in st.session_state
    }
    if payload.get("attempt_token"):
        db.save_assessment_draft(candidate_id, payload)


def save_assessment_answer(candidate_id: int, question_id: int) -> None:
    answer = st.session_state.get(f"answer_{question_id}", "")
    st.session_state.setdefault("assessment_responses", {})[question_id] = answer
    save_current_assessment_draft(candidate_id)


def restore_assessment_draft(draft: dict) -> None:
    """Restore session state from a saved draft and rehydrate answer widgets."""
    for key in ASSESSMENT_DRAFT_KEYS:
        if key in draft:
            st.session_state[key] = draft[key]
    for key in ("assessment_mcq_options", "assessment_responses", "assessment_essay_started_at"):
        if isinstance(st.session_state.get(key), dict):
            st.session_state[key] = {
                int(qid): val for qid, val in st.session_state[key].items()
            }
    for question_id, answer in st.session_state.get("assessment_responses", {}).items():
        st.session_state[f"answer_{question_id}"] = answer


def hide_login_sidebar() -> None:
    """Hide Streamlit's multipage navigation before authentication."""
    st.markdown(
        """<style>
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stSidebarCollapsedControl"] { display: none; }
        </style>""",
        unsafe_allow_html=True,
    )


def hide_app_sidebar_link() -> None:
    """Remove the root app entry from authenticated multipage navigation."""
    st.markdown(
        """<style>
        [data-testid="stSidebarNav"] a[href$="/"] { display: none; }
        [data-testid="stSidebarNav"] a[href$="/app"] { display: none; }
        </style>""",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# MCQ helpers
# ---------------------------------------------------------------------------
def question_options(question: dict) -> list:
    """Return MCQ options regardless of whether the DB driver decoded JSON."""
    raw_options = question.get("options")
    if isinstance(raw_options, str):
        raw_options = json.loads(raw_options)
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError(
            f"Question {question.get('id', '')} has invalid Multiple Choice options."
        )
    return [str(opt) for opt in raw_options]


DIFFICULTY_RATIOS = {"easy": 0.30, "moderate": 0.50, "difficult": 0.20}
DIFFICULTY_TIE_ORDER = {"moderate": 0, "easy": 1, "difficult": 2}


def difficulty_targets(question_count: int) -> dict:
    exact_targets = {d: question_count * r for d, r in DIFFICULTY_RATIOS.items()}
    targets = {d: int(c) for d, c in exact_targets.items()}
    remaining = question_count - sum(targets.values())
    ranked = sorted(
        DIFFICULTY_RATIOS,
        key=lambda d: (-(exact_targets[d] - targets[d]), DIFFICULTY_TIE_ORDER[d]),
    )
    for d in ranked[:remaining]:
        targets[d] += 1
    return targets


def select_by_difficulty(pool, question_count, kind, rng):
    from question_types import QUESTION_TYPE_LABELS

    targets = difficulty_targets(question_count)
    difficulty_pools = {
        d: [q for q in pool if q.get("difficulty", "moderate") == d]
        for d in DIFFICULTY_RATIOS
    }
    shortages = [
        f"{targets[d]} {d} (only {len(difficulty_pools[d])} available)"
        for d in DIFFICULTY_RATIOS
        if len(difficulty_pools[d]) < targets[d]
    ]
    if shortages:
        raise ValueError(
            f"This discipline needs {', '.join(shortages)} "
            f"{QUESTION_TYPE_LABELS[kind]} questions to follow the "
            "30% easy, 50% moderate, 20% difficult mix."
        )
    selected = [
        q
        for d in DIFFICULTY_RATIOS
        for q in rng.sample(difficulty_pools[d], targets[d])
    ]
    rng.shuffle(selected)
    return selected


def select_assessment_questions(bank, settings, rng):
    """Select questions with the required difficulty mix and MCQ subject-topic alignment."""
    pools = {kind: [q for q in bank if q["q_type"] == kind] for kind in QUESTION_TYPES}
    selected = {"mcq": select_by_difficulty(pools["mcq"], settings["mcq"], "mcq", rng)}
    selected_subject_topics = {
        (q.get("subject", "General"), q.get("topic_group", "General"))
        for q in selected["mcq"]
    }
    for kind in REVIEWER_SCORED_TYPES:
        aligned_pool = [
            q for q in pools[kind]
            if (q.get("subject", "General"), q.get("topic_group", "General"))
            in selected_subject_topics
        ]
        selected[kind] = select_by_difficulty(aligned_pool, settings[kind], kind, rng)
    return selected


# ---------------------------------------------------------------------------
# Bootstrap / login gate
# ---------------------------------------------------------------------------
render_logo()
st.title("Competency Technical Assessment (CTA) Portal")
st.caption("Technical assessments · Multiple disciplines · Evidence-based grading")

if not cached_has_users():
    hide_login_sidebar()
    st.subheader("Initial administrator setup")
    st.info(
        "Create the first administrator on a trusted local connection "
        "before exposing this app to the network."
    )

    # Inline bootstrap form (cannot use pages/_shared.account_form here because
    # the database is not yet seeded and imports may not be safe).
    password_key = "bootstrap_password"
    confirm_key = "bootstrap_confirm_password"
    generated_key = "bootstrap_generated_password"
    field_reset = st.session_state.get("bootstrap_reset", 0)
    name_key = f"bootstrap_full_name_{field_reset}"
    username_key = f"bootstrap_username_{field_reset}"

    def _suggest_username_bootstrap():
        full_name = st.session_state.get(name_key, "")
        base = re.sub(r"[^a-z0-9]+", ".", full_name.lower()).strip(".")
        if base:
            st.session_state[username_key] = base

    def _generate_bootstrap_password():
        generated = db.generate_password()
        st.session_state[password_key] = generated
        st.session_state[confirm_key] = generated
        st.session_state[generated_key] = generated

    name = st.text_input("Full name *", key=name_key, on_change=_suggest_username_bootstrap)
    username = st.text_input("Username *", key=username_key)

    with st.form("bootstrap_form"):
        account_email = st.text_input("Email *")
        password = st.text_input(
            "Password (at least 6 characters)", type="password", key=password_key
        )
        confirm = st.text_input("Confirm password", type="password", key=confirm_key)
        st.form_submit_button("Generate random password", on_click=_generate_bootstrap_password)
        if st.form_submit_button("Create account", type="primary"):
            try:
                if password != confirm:
                    raise ValueError("Passwords do not match.")
                db.create_user(username, name, password, "Admin", None, True, email=account_email)
                clear_read_caches()
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    if generated_key in st.session_state:
        st.caption("Copy this generated password:")
        st.code(st.session_state[generated_key], language=None)
    st.stop()

# ---------------------------------------------------------------------------
# Login form
# ---------------------------------------------------------------------------
if "user" not in st.session_state:
    hide_login_sidebar()
    if timeout_message := st.session_state.pop("timeout_message", None):
        st.error(timeout_message)
    if st.session_state.pop("password_changed", False):
        st.success("Password changed. Sign in with your new password.")
    if st.session_state.pop("assessment_submitted", False):
        st.success("Assessment submitted successfully. You have been logged out.")

    login_container = st.empty()
    with login_container.container():
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign in", type="primary"):
                if time.time() < st.session_state.get("retry_after", 0):
                    st.error("Please wait a few seconds before trying again.")
                else:
                    user = db.authenticate(username, password)
                    if user:
                        if db.maintenance_mode() and user["role"] != "Admin":
                            st.warning(
                                "The portal is temporarily unavailable while maintenance is "
                                "in progress. Please try again later."
                            )
                            st.stop()
                        login_token = secrets.token_urlsafe(32)
                        if not db.claim_login(user["id"], login_token):
                            st.error("This account is already logged in on another session.")
                            st.stop()
                        login_container.empty()
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.login_token = login_token
                        if user["role"] == "Candidate":
                            st.session_state.show_candidate_start_dialog = True
                        st.rerun()
                    else:
                        st.session_state.retry_after = time.time() + 3
                        st.error("Invalid username or password.")
    st.stop()

# ---------------------------------------------------------------------------
# Session validation and heartbeat
# ---------------------------------------------------------------------------
user = st.session_state.user
login_token = st.session_state.get("login_token")
if not login_token:
    st.session_state.clear()
    st.error("Your login session is invalid. Please sign in again.")
    st.stop()

now = time.time()
last_refresh = st.session_state.get("last_login_refresh", 0)
if now - last_refresh > 60:
    refreshed_user = db.refresh_login(user["id"], login_token)
    if not refreshed_user:
        st.session_state.clear()
        st.session_state.timeout_message = (
            "You were signed out after 30 minutes of inactivity. Please sign in again."
        )
        st.rerun()
    user = refreshed_user
    st.session_state.user = user
    st.session_state.last_login_refresh = now

if db.maintenance_mode() and user["role"] != "Admin":
    db.release_login(user["id"], login_token)
    st.session_state.clear()
    st.warning(
        "The portal is temporarily unavailable while maintenance is in progress. "
        "Please try again later."
    )
    st.stop()

hide_app_sidebar_link()

# ---------------------------------------------------------------------------
# Admin / Reviewer: redirect to pages via sidebar
# ---------------------------------------------------------------------------
if user["role"] != "Candidate":
    try:
        st.logo("img/Icon/CAT Icon White Background.png", icon_image="img/Icon/CAT-Tab-Icon.png")
    except AttributeError:
        st.sidebar.image("img/Icon/CAT Icon White Background.png", use_container_width=True)
    st.sidebar.write(f"**{user['name']}**")
    st.sidebar.caption(user["role"])

    # Change password expander
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
                    "New password (at least 6 characters)", type="password",
                    key="change_new_password",
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
                        db.release_login(user["id"], login_token)
                        st.session_state.clear()
                        st.session_state.password_changed = True
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if generated := st.session_state.get("change_generated_password"):
                st.caption("Copy your generated password before saving:")
                st.code(generated, language=None)

    if st.sidebar.button("Sign out"):
        db.release_login(user["id"], login_token)
        st.session_state.clear()
        st.rerun()

    # Prompt staff to use the sidebar navigation to reach the pages.
    st.info(
        "Use the sidebar navigation to access Candidate Schedules, Question Bank, "
        "Review Assessments, and other administrative pages."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Candidate assessment runner
# ---------------------------------------------------------------------------
if user["role"] == "Candidate" and st.session_state.pop("show_candidate_start_dialog", False):
    if hasattr(st, "dialog"):
        @st.dialog("Assessment Ready")
        def _candidate_start_dialog():
            st.write(
                "Your assessment is ready. Click the button below to review your details "
                "and start the test."
            )
            if st.button("Click to Start Assessment Test", type="primary"):
                st.session_state.candidate_start_prompt_seen = True
                st.rerun()
        _candidate_start_dialog()
    else:
        st.info("Your assessment is ready. Review your details below, then start the test.")

try:
    st.logo("img/Icon/CAT Icon White Background.png", icon_image="img/Icon/CAT-Tab-Icon.png")
except AttributeError:
    st.sidebar.image("img/Icon/CAT Icon White Background.png", use_container_width=True)
st.sidebar.write(f"**{user['name']}**")
st.sidebar.caption(user["role"])

if st.sidebar.button("Sign out"):
    db.release_login(user["id"], login_token)
    st.session_state.clear()
    st.rerun()

st.subheader("Take an assessment")

discipline = user.get("scheduled_discipline") or user.get("discipline", "")
if not discipline:
    st.info("No discipline is assigned to this candidate.")
    st.stop()
if discipline not in cached_disciplines():
    st.info("No assessments are currently available.")
    st.stop()

bank = cached_questions(discipline)
settings = cached_assessment_settings(user["id"])
question_pools = {kind: [q for q in bank if q["q_type"] == kind] for kind in QUESTION_TYPES}
if any(len(question_pools[kind]) < settings[kind] for kind in QUESTION_TYPES):
    st.error(
        f"This discipline needs {settings['mcq']} MCQ, "
        f"{settings['essay']} Essay, and {settings['oral_practical']} Oral-Practical questions."
    )
    st.stop()

# Restore or initialise assessment state for this discipline.
if st.session_state.get("assessment_discipline") != discipline:
    for key in list(st.session_state):
        if isinstance(key, str) and (
            key.startswith("assessment_")
            or key.startswith("answer_")
            or key in ("candidate_details", "candidate_discipline_display", "candidate_job_title")
        ):
            del st.session_state[key]
    draft = db.assessment_draft(user["id"])
    if (
        draft
        and draft.get("assessment_discipline") == discipline
        and draft.get("attempt_token")
    ):
        restore_assessment_draft(draft)
        st.session_state.assessment_draft_restored = True
    else:
        st.session_state.assessment_discipline = discipline
        st.session_state.attempt_token = secrets.token_hex(24)

# ---------------------------------------------------------------------------
# Candidate details / start screen
# ---------------------------------------------------------------------------
details = st.session_state.get("candidate_details")
if not details:
    st.subheader("Candidate Details")
    st.info(
        "**Candidate instructions**\n\n"
        "- Be presentable and maintain a professional appearance and conduct throughout the "
        "assessment, including the Oral-Practical portion.\n"
        "- You have 40 minutes to answer all Multiple Choice Questions. The countdown begins "
        "when you press the Start Multiple Choice Questions button."
    )
    with st.form("candidate_details_form"):
        st.text_input("Discipline", value=discipline, disabled=True, key="candidate_discipline_display")
        designation = st.selectbox(
            "Job Title",
            ["Inspector", "Supervisor", "Technician"],
            key="candidate_job_title",
        )
        if st.form_submit_button("Start Multiple Choice Questions", type="primary"):
            if not str(designation).strip():
                st.error("Complete all candidate details before starting the assessment.")
            else:
                st.session_state.candidate_details = {
                    "name": user["name"],
                    "email": user.get("email", ""),
                    "designation": str(designation).strip(),
                    "iqama_no": user.get("iqama_no", ""),
                    "employee_no": user.get("employee_no", ""),
                    "exam_date": user.get("test_date") or date.today(),
                    "project_assignment": user.get("project_assignment", ""),
                }
                rng = secrets.SystemRandom()
                try:
                    selected = select_assessment_questions(bank, settings, rng)
                    selected_mcqs = selected["mcq"]
                    st.session_state.assessment_mcq_ids = [q["id"] for q in selected["mcq"]]
                    st.session_state.assessment_essay_ids = [q["id"] for q in selected["essay"]]
                    st.session_state.assessment_reviewer_ids = [
                        q["id"] for q in selected["oral_practical"]
                    ]
                    st.session_state.assessment_mcq_options = {
                        q["id"]: rng.sample(question_options(q), len(question_options(q)))
                        for q in selected_mcqs
                    }
                    # SERVER-SIDE TIMER: deadline is set here and stored in the draft.
                    # On browser refresh the original deadline is restored from the DB,
                    # so candidates cannot gain extra time by reloading.
                    started_at = time.time()
                    st.session_state.assessment_mcq_deadline = started_at + MCQ_TIME_LIMIT_SECONDS
                    st.session_state.assessment_essay_started_at = {}
                    st.session_state.assessment_essay_index = 0
                    st.session_state.assessment_counts = {kind: settings[kind] for kind in QUESTION_TYPES}
                    st.session_state.assessment_phase = "mcq"
                    save_current_assessment_draft(user["id"])
                    st.rerun()
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    st.error(f"Unable to start the Competency Technical Assessment: {exc}")
    st.stop()

# ---------------------------------------------------------------------------
# Assessment runner
# ---------------------------------------------------------------------------
question_map = {q["id"]: q for q in bank}
mcq_questions = [question_map[qid] for qid in st.session_state.assessment_mcq_ids]
essay_questions = [
    question_map[qid]
    for qid in st.session_state.assessment_essay_ids
    if question_map[qid]["q_type"] == "essay"
]
responses = st.session_state.setdefault("assessment_responses", {})

if st.session_state.pop("assessment_draft_restored", False):
    st.success("Your saved assessment answers have been restored.")

st.info(
    f"Complete {settings['mcq']} Multiple Choice Questions and "
    f"{settings['essay']} Essay questions in the app. "
    f"Oral-Practical questions ({settings['oral_practical']}) are completed and graded by a Reviewer."
)

# ---- MCQ phase ----
if st.session_state.get("assessment_phase", "mcq") == "mcq":
    section = st.expander("Multiple Choice Questions", expanded=True)
    section.__enter__()
    st.subheader("Multiple Choice Questions")

    # Server-side deadline: restored from draft on refresh, so no extra time is granted.
    mcq_deadline = st.session_state.get(
        "assessment_mcq_deadline", time.time() + MCQ_TIME_LIMIT_SECONDS
    )
    st.session_state.assessment_mcq_deadline = mcq_deadline
    countdown_timer("Time remaining for all Multiple Choice Questions", mcq_deadline, "mcq")
    is_mcq_expired = time.time() > mcq_deadline

    if is_mcq_expired:
        st.warning(
            "The 40-minute Multiple Choice time limit has expired. "
            "Selected answers will be saved as you continue."
        )

    pending_unanswered = st.session_state.get("assessment_mcq_pending_unanswered", 0)
    if pending_unanswered:
        st.warning(
            f"You have {pending_unanswered} unanswered Multiple Choice question(s). "
            "Return to the questions to complete them, or proceed with those answers scored as zero."
        )
        return_col, proceed_col = st.columns(2)
        if return_col.button("Return to unanswered questions", type="primary"):
            st.session_state.pop("assessment_mcq_pending_unanswered", None)
            st.rerun()
        if proceed_col.button("Proceed with unanswered questions"):
            for question in mcq_questions:
                answer = st.session_state.get(f"answer_{question['id']}")
                responses[question["id"]] = (
                    answer if isinstance(answer, str) and answer.strip() else "[Unanswered]"
                )
            st.session_state.assessment_mcq_unanswered_count = pending_unanswered
            st.session_state.pop("assessment_mcq_pending_unanswered", None)
            st.session_state.assessment_phase = "essay"
            save_current_assessment_draft(user["id"])
            st.rerun()
    else:
        for number, question in enumerate(mcq_questions, 1):
            st.radio(
                f"{number}. {question['question_text']}",
                st.session_state.assessment_mcq_options[question["id"]],
                index=None,
                key=f"answer_{question['id']}",
                disabled=is_mcq_expired,
                on_change=save_assessment_answer,
                args=(user["id"], question["id"]),
            )
        st.info(
            "Each selected answer is saved automatically. "
            "You have six minutes for each Essay question after continuing."
        )
        submit_label = (
            "Time expired: Proceed to Essay Questions"
            if is_mcq_expired
            else "Continue to Essay Questions"
        )
        if st.button(submit_label, type="primary"):
            unanswered_count = sum(
                not isinstance(responses.get(q["id"]), str) or not responses[q["id"]].strip()
                for q in mcq_questions
            )
            if unanswered_count and not is_mcq_expired:
                st.session_state.assessment_mcq_pending_unanswered = unanswered_count
                save_current_assessment_draft(user["id"])
                st.rerun()
            else:
                for question in mcq_questions:
                    if question["id"] not in responses or not str(responses[question["id"]]).strip():
                        responses[question["id"]] = "[Unanswered - time expired]"
                st.session_state.assessment_mcq_unanswered_count = unanswered_count
                st.session_state.assessment_phase = "essay"
                save_current_assessment_draft(user["id"])
                st.rerun()
    section.__exit__(None, None, None)

# ---- Essay phase ----
else:
    section = st.expander("Essay Questions", expanded=True)
    section.__enter__()
    st.subheader("Essay Questions")
    st.info(
        "Each Essay question has six minutes. "
        "Oral-Practical questions are completed and graded by a Reviewer."
    )

    if unanswered_count := st.session_state.pop("assessment_mcq_unanswered_count", 0):
        st.warning(
            f"{unanswered_count} Multiple Choice question(s) were left unanswered "
            "and will receive no score."
        )

    essay_index = st.session_state.setdefault("assessment_essay_index", 0)

    if essay_index >= len(essay_questions):
        st.success("All Essay questions are complete. Submit the assessment when ready.")
        if st.button("Submit assessment", type="primary"):
            for q in essay_questions:
                if q["id"] not in responses or not responses[q["id"]].strip():
                    responses[q["id"]] = "[No response submitted - time expired]"
            try:
                db.submit(
                    user["id"],
                    discipline,
                    responses,
                    st.session_state.attempt_token,
                    st.session_state.candidate_details,
                    (
                        st.session_state.assessment_mcq_ids
                        + st.session_state.assessment_essay_ids
                        + st.session_state.assessment_reviewer_ids
                    ),
                    point_settings={kind: settings[f"{kind}_points"] for kind in QUESTION_TYPES},
                    expected_counts=st.session_state.get("assessment_counts"),
                )
                db.delete_assessment_draft(user["id"])
                clear_read_caches()
                db.release_login(user["id"], st.session_state.login_token)
                st.session_state.clear()
                st.session_state.assessment_submitted = True
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    else:
        question = essay_questions[essay_index]
        essay_started_at = st.session_state.setdefault("assessment_essay_started_at", {})

        # SERVER-SIDE TIMER: essay start times are stored in the draft.
        # Refreshing the browser reuses the original start time.
        if question["id"] not in essay_started_at:
            essay_started_at[question["id"]] = time.time()
            save_current_assessment_draft(user["id"])

        started_at = essay_started_at[question["id"]]
        deadline = started_at + ESSAY_TIME_LIMIT_SECONDS
        expired = time.time() >= deadline

        st.caption(f"Essay Question {essay_index + 1} of {len(essay_questions)}")
        countdown_timer(
            f"Time remaining for Essay question {essay_index + 1} of {len(essay_questions)}",
            deadline,
            f"essay-{question['id']}",
        )
        if expired:
            st.warning("Essay time expired. Click below to proceed to the next question.")

        current_val = responses.get(question["id"], "")
        answer = st.text_area(
            f"{essay_index + 1}. Essay: {question['question_text']}",
            value=current_val,
            placeholder="Type your answer here...",
            height=220,
            max_chars=20000,
            key=f"answer_{question['id']}",
            disabled=expired,
            on_change=save_assessment_answer,
            args=(user["id"], question["id"]),
        )
        st.caption("Your response is saved automatically while you work.")
        btn_label = (
            "Time expired: Go to next question"
            if expired
            else "Save answer and go to next question"
        )
        if st.button(btn_label, type="primary"):
            if expired and not answer.strip():
                responses[question["id"]] = "[No response submitted - time expired]"
            else:
                responses[question["id"]] = answer.strip()
            st.session_state.assessment_essay_index = essay_index + 1
            save_current_assessment_draft(user["id"])
            st.rerun()

    section.__exit__(None, None, None)
