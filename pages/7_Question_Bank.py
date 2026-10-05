"""Question Bank page - import, export, browse, archive, delete, and wipe questions."""
import json

import streamlit as st

import database as db
from question_import import QuestionImportError, export_questions_bytes, parse_questions, template_bytes
from shared import (
    inject_global_styles,
    render_logo,
    require_login,
    sidebar_nav,
    cached_disciplines,
    cached_question_count,
    cached_question_counts,
    cached_question_page,
    cached_questions,
    clear_read_caches,
)
from question_types import QUESTION_TYPE_LABELS

st.set_page_config(
    page_title="Question Bank - CTA Portal",
    page_icon=":material/quiz:",
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
st.subheader("Question Bank")
st.caption("Add project-specific technical questions and rubrics before using this for hiring.")

if st.session_state.pop("question_bank_deleted", False):
    st.success(
        "Questions deleted from bank. Unanswered questions were removed. Questions already used in candidate submissions were archived and kept linked to historical assessment records."
    )


def clear_question_data():
    st.session_state.pop("question_export_bytes", None)
    clear_read_caches()


def refresh_question_bank_page():
    """Return to the Question Bank after a mutation, preserving page context."""
    st.switch_page("pages/7_Question_Bank.py")

# ---------------------------------------------------------------------------
# Import / Export controls
# ---------------------------------------------------------------------------
template_column, export_column = st.columns(2)
template_column.download_button(
    "Download Excel template",
    template_bytes(),
    "qc-question-template.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    width="stretch",
)
with export_column:
    active_count = sum(cached_question_counts().values())
    if st.button(
        f"Prepare question export ({active_count})",
        width="stretch",
        disabled=active_count == 0,
    ):
        with st.spinner("Preparing Excel export..."):
            st.session_state.question_export_bytes = export_questions_bytes(cached_questions())
    if export_bytes := st.session_state.get("question_export_bytes"):
        st.download_button(
            "Download prepared export",
            export_bytes,
            "qc-existing-questions.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )


def keep_question_import_open():
    st.session_state.question_import_expanded = True


def close_question_import():
    """Close the dialog and reset its upload and result state."""
    st.session_state.pop("question_import_result", None)
    st.session_state.question_import_upload_version = (
        st.session_state.get("question_import_upload_version", 0) + 1
    )
    st.session_state.question_import_expanded = False

with st.expander(
    "Import questions from Excel",
    expanded=st.session_state.get("question_import_expanded", False),
):
    st.caption(
        "Step 1 of 2: Select the completed Excel template. "
        "Step 2 of 2: Import the selected questions."
    )
    upload = st.file_uploader(
        "1. Select Excel file",
        type=["xlsx"],
        key=f"question_import_workbook_{st.session_state.get('question_import_upload_version', 0)}",
        help="Use the downloaded template. Existing questions are not changed.",
        on_change=keep_question_import_open,
    )
    import_requested = st.button("2. Import Questions", type="primary", disabled=upload is None)

    if upload is not None and import_requested:
        st.session_state.pop("question_import_result", None)
        if hasattr(st, "dialog"):
            @st.dialog("Importing Questions", width="large")
            def _import_dialog():
                stage = st.empty()
                result = st.session_state.get("question_import_result")
                if result is None:
                    stage.info("Step 1 of 2: Validating the Excel workbook. No questions are being added yet.")
                    progress_bar = st.progress(0, text="Validating Excel workbook...")
                    phase = 1
                    try:
                        parsed_results = parse_questions(upload.getvalue())
                        valid_count = sum(1 for r in parsed_results if r["success"])
                        invalid_count = len(parsed_results) - valid_count
                        progress_bar.empty()
                        stage.info(
                            f"Step 2 of 2: Importing {valid_count} validated question(s) into the "
                            f"question bank. {invalid_count} row(s) will be reported as invalid."
                        )
                        progress_bar = st.progress(0, text="Importing validated questions...")
                        phase = 2

                        def import_progress(current, total):
                            progress_bar.progress(
                                current / total if total > 0 else 1.0,
                                text=f"Import progress: question {current} of {total}...",
                            )

                        final_results = db.add_questions(
                            user["id"], parsed_results, progress_callback=import_progress
                        )
                        clear_question_data()
                        success_count = sum(1 for r in final_results if r["success"])
                        result = {
                            "success_count": success_count,
                            "fail_count": len(final_results) - success_count,
                            "rows": [
                                {
                                    "Row": r["row_number"],
                                    "Status": "Success" if r["success"] else "Failed",
                                    "Error": r["error"] or "",
                                    "Preview": (
                                        (r.get("prompt") or "")[:80] + "..."
                                        if len(r.get("prompt") or "") > 80
                                        else (r.get("prompt") or "")
                                    ),
                                }
                                for r in final_results
                            ],
                        }
                        st.session_state.question_import_result = result
                        progress_bar.empty()
                    except (QuestionImportError, ValueError) as exc:
                        progress_bar.empty()
                        result = {
                            "error": str(exc),
                            "phase": phase,
                        }
                        st.session_state.question_import_result = result

                if result.get("error"):
                    if result["phase"] == 1:
                        stage.error("Step 1 of 2: Validation failed. No questions were imported.")
                    else:
                        stage.error("Step 2 of 2: Import failed after validation completed.")
                    st.error(result["error"])
                else:
                    stage.success("Import complete.")
                    if result["fail_count"] == 0:
                        st.success(f"{result['success_count']} questions imported successfully.")
                    else:
                        st.warning(
                            f"Import finished: {result['success_count']} succeeded, "
                            f"{result['fail_count']} failed."
                        )
                    st.dataframe(result["rows"], width="stretch")

                if st.button("Close"):
                    close_question_import()
                    st.rerun()

            _import_dialog()
        else:
            # Fallback for older Streamlit versions without st.dialog.
            stage = st.empty()
            stage.info("Step 1 of 2: Validating the Excel workbook. No questions are being added yet.")
            progress_bar = st.progress(0, text="Validating Excel workbook...")
            try:
                parsed_results = parse_questions(upload.getvalue())
                valid_count = sum(1 for r in parsed_results if r["success"])
                progress_bar.progress(1.0, text="Validation complete.")
                stage.info(f"Importing {valid_count} question(s)...")
                final_results = db.add_questions(user["id"], parsed_results)
                clear_read_caches()
                stage.success("Import finished.")
                st.dataframe(
                    [{"Row": r["row_number"], "Status": r["success"], "Error": r["error"] or ""} for r in final_results],
                    width="stretch",
                )
            except (QuestionImportError, ValueError) as exc:
                stage.error(str(exc))

# ---------------------------------------------------------------------------
# Browse / filter questions
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Browse questions")

disciplines = cached_disciplines()
discipline_counts = cached_question_counts()
discipline_options = ["All"] + disciplines
discipline_labels = {
    "All": f"All - {sum(discipline_counts.values())}",
    **{
        discipline: f"{discipline} - {discipline_counts.get(discipline, 0)}"
        for discipline in disciplines
    },
}

type_options = {k: v for k, v in QUESTION_TYPE_LABELS.items()}
type_options_all = {"": "All types", **type_options}
candidate_role_options = {
    "": "All candidate roles",
    "Inspector": "Inspector",
    "Supervisor": "Supervisor",
    "Technician": "Technician",
}

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    filter_discipline = st.selectbox(
        "Discipline",
        discipline_options,
        format_func=lambda discipline: discipline_labels[discipline],
        key="qb_filter_discipline",
    )
with filter_col2:
    filter_type = st.selectbox(
        "Question type",
        list(type_options_all.keys()),
        format_func=lambda k: type_options_all[k],
        key="qb_filter_type",
    )
with filter_col3:
    filter_candidate_role = st.selectbox(
        "Candidate role",
        list(candidate_role_options),
        format_func=lambda role: candidate_role_options[role],
        key="qb_filter_candidate_role",
    )
filter_signature = (filter_discipline, filter_type, filter_candidate_role)
if st.session_state.get("qb_filter_signature") != filter_signature:
    st.session_state.qb_filter_signature = filter_signature
    st.session_state.qb_page = 1

page_size = 20
selected_discipline = None if filter_discipline == "All" else filter_discipline
total_questions = cached_question_count(
    selected_discipline, filter_type or None, filter_candidate_role or None
)
st.caption(f"{total_questions} question(s) match the current filters.")

if not total_questions:
    st.info("No questions match the selected filters.")
else:
    total_pages = max(1, (total_questions + page_size - 1) // page_size)
    st.session_state.qb_page = min(st.session_state.get("qb_page", 1), total_pages)
    if total_pages > 1:
        p_col1, p_col2 = st.columns([1, 3])
        with p_col1:
            page_num = st.number_input(
                "Page", min_value=1, max_value=total_pages, step=1, key="qb_page"
            )
        with p_col2:
            st.caption(
                f"Showing questions {(page_num - 1) * page_size + 1} "
                f"to {min(page_num * page_size, total_questions)} "
                f"of {total_questions}"
            )
    else:
        page_num = 1

    _, page_questions = cached_question_page(
        selected_discipline,
        filter_type or None,
        page_size,
        (page_num - 1) * page_size,
        candidate_role=filter_candidate_role or None,
    )

    for q in page_questions:
        with st.expander(
            f"#{q['id']} · {q['discipline']} · "
            f"{type_options.get(q['q_type'], q['q_type'])} · "
            f"{'Active' if q['active'] else 'Archived'}"
        ):
            st.write(q["question_text"])
            role_display = q.get('candidate_role')
            if not role_display or role_display in ('All', ''):
                role_display = 'Inspector'
            st.caption(f"Candidate role: {role_display}")
            if q["q_type"] == "mcq":
                options_list = json.loads(q["options"]) if q.get("options") else []
                for opt in options_list:
                    if opt == q["correct_answer"]:
                        st.markdown(f"- **{opt}** (correct)")
                    else:
                        st.markdown(f"- {opt}")
            else:
                st.write(q["rubric"])

            if q.get("is_used"):
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if st.button(
                        "Archive" if q["active"] else "Restore", key=f"active_{q['id']}"
                    ):
                        db.set_active(user["id"], q["id"], not q["active"])
                        clear_read_caches()
                        refresh_question_bank_page()
                with col_btn2:
                    if not q["active"]:
                        if st.button(
                            "Delete permanently (removes linked submissions)",
                            key=f"hard_delete_{q['id']}",
                            type="primary",
                        ):
                            try:
                                db.delete_question(user["id"], q["id"], force=True)
                                clear_read_caches()
                                refresh_question_bank_page()
                            except ValueError as exc:
                                st.error(str(exc))
            else:
                if st.button("Delete", key=f"delete_{q['id']}"):
                    try:
                        db.delete_question(user["id"], q["id"])
                        clear_read_caches()
                        refresh_question_bank_page()
                    except ValueError as exc:
                        st.error(str(exc))

# ---------------------------------------------------------------------------
# Admin-only: wipe controls
# ---------------------------------------------------------------------------
if user["role"] == "Admin":
    st.divider()

    def _render_question_bank_wipe():
        with st.expander("Delete Questions from Bank"):
            st.warning(
                "This clears the active question bank based on your selection. Any question that has already appeared in a candidate submission is archived so historical assessment records remain linked to the original question."
            )
            
            wipe_discipline = st.selectbox("Select Discipline to Delete", ['All Disciplines'] + db.disciplines(), key="wipe_discipline_select")
            wipe_role = st.selectbox("Select Candidate Role to Delete", ['All Roles', 'Inspector', 'Supervisor', 'Technician'], key="wipe_role_select")

            if st.button("Delete Questions from Bank", type="primary"):
                if hasattr(st, "dialog"):
                    @st.dialog("Confirm Delete Questions")
                    def _wipe_question_bank_dialog(discipline, role):
                        st.warning(
                            f"This removes all unanswered questions for {discipline} and {role}, and archives only the questions that were already used in candidate assessments."
                        )
                        if st.button("Confirm Delete Questions", type="primary"):
                            progress_bar = st.progress(0, text="Preparing to delete questions...")

                            def wipe_progress(current, total, text):
                                progress_bar.progress(
                                    current / total if total > 0 else 1.0,
                                    text=text,
                                )

                            try:
                                db.wipe_questions(user["id"], discipline, role, progress_callback=wipe_progress)
                                clear_read_caches()
                                progress_bar.empty()
                                st.session_state["question_bank_deleted"] = True
                                st.rerun()
                            except ValueError as exc:
                                progress_bar.empty()
                                st.error(str(exc))
                    _wipe_question_bank_dialog(wipe_discipline, wipe_role)
                else:
                    st.session_state["confirm_wipe_question_bank"] = True
            if st.session_state.get("confirm_wipe_question_bank"):
                st.warning(
                    f"This removes all unanswered questions for {wipe_discipline} and {wipe_role}, and archives only the questions that were already used in candidate assessments."
                )
                if st.button("Confirm Delete Questions", type="primary"):
                    progress_bar = st.progress(0, text="Preparing to delete questions...")

                    def wipe_progress(current, total, text):
                        progress_bar.progress(
                            current / total if total > 0 else 1.0,
                            text=text,
                        )

                    try:
                        db.wipe_questions(user["id"], wipe_discipline, wipe_role, progress_callback=wipe_progress)
                        clear_read_caches()
                        progress_bar.empty()
                        st.session_state.pop("confirm_wipe_question_bank", None)
                        st.session_state["question_bank_deleted"] = True
                        st.rerun()
                    except ValueError as exc:
                        progress_bar.empty()
                        st.error(str(exc))

            st.error(
                "The following option is destructive. It permanently deletes archived question records and removes any candidate submission that references them."
            )
            if st.button("Permanently delete archived questions and linked submissions"):
                if hasattr(st, "dialog"):
                    @st.dialog("Deleting Archived Questions")
                    def _wipe_archived_dialog():
                        st.warning(
                            "This permanently deletes archived question records and any candidate submission that references them."
                        )
                        confirmed = st.checkbox(
                            "I understand that archived question records and their linked candidate submissions cannot be recovered."
                        )
                        if st.button(
                            "Permanently delete archived questions and linked submissions",
                            type="primary",
                            disabled=not confirmed,
                        ):
                            progress_bar = st.progress(0, text="Preparing to delete...")

                            def wipe_progress(current, total):
                                text = (
                                    "Removing affected candidate records..."
                                    if current == 0
                                    else f"Deleted {total} archived questions."
                                )
                                progress_bar.progress(
                                    current / total if total > 0 else 1.0, text=text
                                )

                            try:
                                deleted_count = db.wipe_archived_questions(
                                    user["id"], progress_callback=wipe_progress
                                )
                                clear_read_caches()
                                progress_bar.empty()
                                st.success(
                                    f"Wipe complete. Deleted {deleted_count} archived question records and their linked submissions."
                                )
                            except ValueError as exc:
                                progress_bar.empty()
                                st.error(str(exc))
                        if st.button("Close"):
                            st.rerun()
                    _wipe_archived_dialog()
                else:
                    st.session_state["confirm_wipe_archived_questions"] = True

            if st.session_state.get("confirm_wipe_archived_questions"):
                confirmed = st.checkbox(
                    "I understand that archived question records and their linked candidate submissions cannot be recovered.",
                    key="confirm_wipe_archived_questions_acknowledged",
                )
                if st.button(
                    "Confirm permanent archive wipe", type="primary", disabled=not confirmed
                ):
                    progress_bar = st.progress(0, text="Preparing to delete...")

                    def wipe_progress(current, total):
                        text = (
                            "Removing affected candidate records..."
                            if current == 0
                            else f"Deleted {total} archived questions."
                        )
                        progress_bar.progress(current / total if total > 0 else 1.0, text=text)

                    try:
                        deleted_count = db.wipe_archived_questions(
                            user["id"], progress_callback=wipe_progress
                        )
                        clear_read_caches()
                        progress_bar.empty()
                        st.session_state.pop("confirm_wipe_archived_questions", None)
                        st.success(
                            f"Wipe complete. Deleted {deleted_count} archived question records and their linked submissions."
                        )
                    except ValueError as exc:
                        progress_bar.empty()
                        st.error(str(exc))

    _render_question_bank_wipe()

