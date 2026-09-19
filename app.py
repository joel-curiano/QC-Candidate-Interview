"""Run with: streamlit run app.py"""
import csv
import base64
import io
import json
import secrets
import time
from datetime import date
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import database as db
from email_service import EmailDeliveryError, send_candidate_invitation, send_candidate_result, send_reviewer_credentials, send_test_email
from question_import import QuestionImportError, export_questions_bytes, parse_questions, template_bytes
from result_export import excel_bytes

CAT_TAB_ICON_PATH = 'img/Icon/CAT Icon Neutral Backgound.jpg'
st.set_page_config(page_title='Competency Technical Assessment (CTA) Portal', page_icon=CAT_TAB_ICON_PATH, layout='centered')
st.markdown(
    '''<style>
    [data-testid="stSidebar"] {
        background-color: #d9dcde;
        width: 285px !important;
        min-width: 285px !important;
        max-width: 285px !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        width: 85% !important;
        margin-left: auto;
        margin-right: auto;
    }
    .cat-theme-icon { display: block; width: 128px; height: 128px; object-fit: contain; margin: 0 0 4px 0; }
    .cat-theme-icon.dark { display: none; }
    [data-testid="stMainBlockContainer"] { padding-top: 3rem; }
    .company-details { color: #4B5563; font-size: 0.82rem; line-height: 1.45; margin: 0.1rem 0 1.2rem 0; }
    .company-details strong { color: #b51f2d; }
    [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {
        position: fixed;
        top: 72px;
        right: 24px;
        width: 380px;
        z-index: 9999;
        background: #ffffff;
        border: 2px solid #b51f2d;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(20, 39, 53, 0.22);
        padding: 6px 12px;
        min-height: 82px;
        overflow: visible;
    }
    [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) iframe {
        width: 100% !important;
        height: 82px !important;
        min-height: 82px !important;
        display: block;
    }
    @media (max-width: 640px) {
        [data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {
            top: 56px;
            right: 10px;
            left: 10px;
            width: auto;
        }
    }
    @media (prefers-color-scheme: dark) {
        .cat-theme-icon.light { display: none; }
        .cat-theme-icon.dark { display: block; }
    }
    [data-testid="stMarkdownContainer"] h3 {
        color: #b51f2d !important;
    }
    .stButton > button,
    .stDownloadButton > button {
        background-color: #ffffff;
        border: 1px solid #b51f2d;
        color: #8f1824;
        font-weight: 600;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background-color: #fce8eb;
        border-color: #8f1824;
        color: #8f1824;
    }
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background-color: #b51f2d;
        border-color: #b51f2d;
        color: #ffffff;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        background-color: #8f1824;
        border-color: #8f1824;
        color: #ffffff;
    }
    .stButton > button:focus-visible,
    .stDownloadButton > button:focus-visible {
        box-shadow: 0 0 0 3px rgba(181, 31, 45, 0.25);
        outline: none;
    }
    .stButton > button:disabled,
    .stDownloadButton > button:disabled {
        background-color: #e2e8f0;
        border-color: #cbd5e1;
        color: #64748b;
    }
    .logo-container {
        text-align: left;
        margin-bottom: 0.5rem;
    }
    .logo-container img {
        width: 240px;
        max-width: 100%;
        margin-left: 0;
    }
    @media (orientation: portrait) {
        .logo-container img {
            max-width: 70% !important;
        }
        h1 {
            font-size: 1.5rem !important;
        }
    }
    </style>''',
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cat_icon_data_url(filename):
    path = Path(__file__).resolve().parent / 'img' / filename
    if not path.exists():
        path = Path('img') / filename
    if not path.exists():
        return ''
    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
    content_type = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
    return f'data:{content_type};base64,{encoded}'





MCQ_TIME_LIMIT_SECONDS = 40 * 60
ESSAY_TIME_LIMIT_SECONDS = 6 * 60


def countdown_timer(label, deadline, key):
    """Display a client-side countdown while keeping the deadline server-side."""
    remaining = max(0, int(deadline - time.time()))
    components.html(f"""
        <div id="timer-{key}" style="font-family:sans-serif;color:#b51f2d;padding:6px 0;text-align:center;min-height:70px;box-sizing:border-box">
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
    """, height=82)


@st.cache_resource(show_spinner=False)
def initialize_database():
    db.init_db()
    db.invalidate_all_logins()
    return True


@st.cache_data(ttl=30, show_spinner=False)
def cached_disciplines():
    return db.disciplines()


@st.cache_data(ttl=30, show_spinner=False)
def cached_questions(discipline=None, include_inactive=False):
    return db.questions(discipline, include_inactive=include_inactive)


@st.cache_data(ttl=30, show_spinner=False)
def cached_assessment_settings(actor_id):
    return db.assessment_settings(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_projects(actor_id):
    return db.get_projects(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_candidate_accounts(actor_id):
    return db.candidate_accounts(actor_id)


@st.cache_data(ttl=60, show_spinner=False)
def cached_submissions(actor_id):
    return db.submissions(actor_id)


@st.cache_data(ttl=300, show_spinner=False)
def cached_candidate_result_pdf(sub_json_str):
    sub = json.loads(sub_json_str)
    return candidate_result_pdf(sub)


@st.cache_data(ttl=600, show_spinner=False)
def cached_has_users():
    return db.has_users()


def clear_read_caches():
    cached_has_users.clear()
    cached_disciplines.clear()
    cached_questions.clear()
    cached_assessment_settings.clear()
    cached_projects.clear()
    cached_candidate_accounts.clear()
    cached_submissions.clear()
    cached_candidate_result_pdf.clear()


def filter_upcoming_candidates(candidates, name='All', discipline='All', iqama_no='All'):
    """Return upcoming candidates matching the current schedule filters."""
    def normalized(value):
        return str(value or '').strip().casefold()

    name_filter = normalized(name)
    discipline_filter = normalized(discipline)
    iqama_filter = normalized(iqama_no)

    return [
        candidate for candidate in candidates
        if (name == 'All' or normalized(candidate.get('name')) == name_filter)
        and (
            discipline == 'All'
            or normalized(candidate.get('scheduled_discipline') or candidate.get('discipline')) == discipline_filter
        )
        and (iqama_no == 'All' or normalized(candidate.get('iqama_no')) == iqama_filter)
    ]


def question_options(question):
    """Return MCQ options regardless of whether the database driver decoded JSON."""
    raw_options = question.get('options')
    if isinstance(raw_options, str):
        raw_options = json.loads(raw_options)
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError(f"Question {question.get('id', '')} has invalid Multiple Choice options.")
    return [str(option) for option in raw_options]


try:
    with st.spinner('Loading Competency Technical Assessment (CTA) Portal...'):
        initialize_database()
except db.DatabaseError as exc:
    st.error(str(exc))
    st.stop()


def account_form(key, bootstrap=False, actor=None, allowed_roles=None):
    password_key = f'{key}_password'
    confirm_key = f'{key}_confirm_password'
    generated_key = f'{key}_generated_password'

    def generate_account_password():
        generated = db.generate_password()
        st.session_state[password_key] = generated
        st.session_state[confirm_key] = generated
        st.session_state[generated_key] = generated

    form_key = f'{key}_{st.session_state.get(f"{key}_reset", 0)}'
    with st.form(form_key):
        name = st.text_input('Full name *')
        username = st.text_input('Username *')
        
        is_candidate = allowed_roles == ['Candidate']
        account_email = st.text_input('Email *') if is_candidate or actor is not None or bootstrap else ''
        
        iqama_no = ''
        employee_no = ''
        mobile_no = ''
        if is_candidate:
            iqama_no = st.text_input('Iqama No *')
            employee_no = st.text_input('Employee No')
            mobile_no = st.text_input('Mobile No')
            
        if is_candidate:
            password = confirm = db.generate_password()
            st.info('Login credentials will be generated and emailed after the assessment is scheduled.')
        else:
            password = st.text_input('Password (at least 6 characters)', type='password', key=password_key)
            confirm = st.text_input('Confirm password', type='password', key=confirm_key)
        role = st.selectbox('Role', allowed_roles or ['Candidate', 'Reviewer', 'Admin']) if actor else 'Candidate'
        if not is_candidate:
            st.form_submit_button('Generate random password', on_click=generate_account_password)

        if st.form_submit_button('Create account', type='primary'):
            try:
                if password != confirm:
                    raise ValueError('Passwords do not match.')
                if is_candidate and not all(value.strip() for value in (name, username, account_email, iqama_no)):
                    raise ValueError('Name, username, email, and Iqama No are required for Candidate accounts.')
                if role == 'Reviewer' and not account_email.strip():
                    raise ValueError('Reviewer email is required so login credentials can be sent.')
                
                candidate_id = db.create_user(
                    username, name, password, role, actor, bootstrap, 
                    email=account_email, test_date=None,
                    discipline='', iqama_no=iqama_no, 
                    employee_no=employee_no, mobile_no=mobile_no
                )
                if role == 'Reviewer':
                    try:
                        send_reviewer_credentials(account_email.strip().lower(), name.strip(), username.strip().lower(), password)
                        st.session_state.pop(generated_key, None)
                        clear_read_caches()
                        st.success('Reviewer account created and login credentials emailed.')
                    except (EmailDeliveryError, OSError, ValueError) as exc:
                        st.warning(f'Account created, but the credentials email could not be sent: {exc}')
                else:
                    st.session_state.pop(generated_key, None)
                    clear_read_caches()
                    st.success('Account created.')
                    if is_candidate:
                        st.session_state[f'{key}_reset'] = st.session_state.get(f'{key}_reset', 0) + 1
                        st.rerun()
                if bootstrap:
                    clear_read_caches()
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    if not is_candidate and generated_key in st.session_state:
        st.caption('Copy this generated password and give it securely to the account owner:')
        st.code(st.session_state[generated_key], language=None)


def result_table(rows):
    return [{'Candidate': r['candidate_name'], 'Job Title': r.get('designation', ''),
             'Employee No': r.get('employee_no', ''),
             'Discipline': r['discipline'], 'Project Assignment': r.get('project_assignment', ''),
             'Exam Date': format_result_datetime(r.get('exam_date', '')), 'Status': r['status'],
             'Multiple Choice Grade': db.category_result(r, 'mcq'),
             'Essay Grade': db.category_result(r, 'essay'),
             'Oral Grade': db.category_result(r, 'oral'),
             'Practical Grade': db.category_result(r, 'practical'),
             'Reviewer Comments': r.get('reviewer_comments', ''), 'Graded (UTC)': format_result_datetime(r.get('graded_at', '')),
             'Overall Result': db.result(r)} for r in rows]


def format_result_datetime(value):
    if not value:
        return ''
    text = str(value).replace('T', ' ').replace('Z', '')
    if '.' in text:
        text = text.split('.', 1)[0]
    if '+' in text[10:]:
        text = text.split('+', 1)[0]
    if len(text) == 10:
        return f'{text} 00:00'
    return text[:16]


def candidate_result_pdf(sub):
    """Create a branded PDF result report in memory."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=27*mm, leftMargin=27*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CATTitle', parent=styles['Title'], textColor=colors.HexColor('#B51F2D'), fontSize=20, leading=24, spaceAfter=8))
    styles.add(ParagraphStyle(name='CATBody', parent=styles['BodyText'], fontSize=10, leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='CATResultHeading', parent=styles['Heading2'], textColor=colors.HexColor('#142735'), fontSize=11, leading=14, alignment=1, spaceBefore=8, spaceAfter=5))
    styles.add(ParagraphStyle(name='CATOverallResult', parent=styles['CATResultHeading'], alignment=1, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name='CATExplainHeading', parent=styles['BodyText'], textColor=colors.HexColor('#142735'), fontSize=8, leading=10, spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyle(name='CATExplainBody', parent=styles['BodyText'], textColor=colors.HexColor('#4B5563'), fontSize=8, leading=10, spaceAfter=0))
    styles.add(ParagraphStyle(name='CATCompany', parent=styles['CATBody'], alignment=1, fontSize=7, leading=9, textColor=colors.HexColor('#4B5563')))
    logo_path = 'img/C.A.T. Logo - Horizontal.jpg'
    logo_width = 35.1 * mm
    logo_source_width, logo_source_height = ImageReader(logo_path).getSize()
    logo_height = logo_width * logo_source_height / logo_source_width
    story = [Image(logo_path, width=logo_width, height=logo_height),
             Paragraph('<b>QUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.</b><br/>Ash Shulah, Dammam 34266, Saudi Arabia', styles['CATCompany']),
             Spacer(1, 2*mm),
             Paragraph('Candidate Assessment Result', styles['CATTitle']),
             Spacer(1, 4*mm)]
    story.append(Paragraph(f"<b>Candidate:</b> {sub.get('candidate_name', '')}<br/><b>Iqama No:</b> {sub.get('iqama_no', '')}<br/><b>Discipline:</b> {sub.get('discipline', '')}<br/><b>Exam date:</b> {format_result_datetime(sub.get('exam_date', ''))}", styles['CATBody']))
    if sub['status'] != 'Graded':
        story.append(Paragraph('<b>Overall result:</b> Pending Review', styles['CATOverallResult']))
    else:
        rows = [['Question type', 'Percentage', 'Status']]
        for kind, label in (('mcq', 'Multiple Choice'), ('essay', 'Essay'), ('oral', 'Oral Test'), ('practical', 'Practical Test')):
            pct = db.category_percentage(sub, kind)
            rows.append([label, f'{pct:.1f}%', 'PASS' if pct >= 50 else 'FAIL'])
        overall_pct = 100 * (sub['mcq_score'] + sub['essay_score'] + sub.get('oral_score', 0) + sub.get('practical_score', 0)) / sub['max_possible_points'] if sub['max_possible_points'] else 0
        overall_status = 'PASS' if overall_pct >= 70 and all(db.category_percentage(sub, kind) >= 50 for kind in ('mcq', 'essay', 'oral', 'practical')) else 'FAIL'
        overall_color = '#188038' if overall_status == 'PASS' else '#B51F2D'
        story += [Spacer(1, 4*mm), Paragraph('Results by question type', styles['CATResultHeading']), Table(rows, colWidths=[39*mm, 26.6*mm, 22.4*mm], style=TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#B51F2D')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#D9DCDE')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('LEADING',(0,0),(-1,-1),10),('PADDING',(0,0),(-1,-1),4)])), Spacer(1, 5*mm), Paragraph(f'<b>Overall result:</b> {overall_pct:.1f}% - <font color="{overall_color}"><b>{overall_status}</b></font>', styles['CATOverallResult'])]
    story += [Spacer(1, 6*mm), Paragraph('<b>How pass/fail is determined</b>', styles['CATExplainHeading']), Paragraph('The candidate must achieve at least 50% in every question type and at least 70% overall. The overall percentage is calculated from the accumulated points earned divided by the total possible points. Failing any one question type results in an overall FAIL, even when the overall percentage is 70% or higher. A result remains Pending Review until the Reviewer scores all Essay, Oral Test, and Practical Test responses.', styles['CATExplainBody'])]
    doc.build(story)
    return output.getvalue()

if hasattr(st, 'dialog'):
    @st.dialog('Email delivery status')
    def send_test_email_dialog(recipient, name):
        status = st.status('Sending test email…', expanded=True)
        try:
            send_test_email(recipient, name)
            status.update(label='Test email sent successfully', state='complete', expanded=True)
            st.success(f'Test email delivered to {recipient}.')
        except (EmailDeliveryError, OSError, ValueError) as exc:
            status.update(label='Test email failed', state='error', expanded=True)
            st.error(str(exc))
        if st.button('Close', key='close_test_email_status'):
            st.rerun()

    @st.dialog('Importing Questions', width='large')
    def import_dialog(file_bytes, uid):
        stage = st.empty()
        stage.info('Step 1 of 2: Validating the Excel workbook. No questions are being added yet.')
        progress_bar = st.progress(0, text='Validating Excel workbook...')
        phase = 1
        try:
            parsed_results = parse_questions(file_bytes)
            valid_count = sum(1 for result in parsed_results if result['success'])
            invalid_count = len(parsed_results) - valid_count
            progress_bar.empty()
            stage.info(
                f'Step 2 of 2: Importing {valid_count} validated question(s) into the question bank. '
                f'{invalid_count} row(s) will be reported as invalid.'
            )
            progress_bar = st.progress(0, text='Importing validated questions...')
            phase = 2
            def import_progress(current, total):
                progress_bar.progress(
                    current / total if total > 0 else 1.0,
                    text=f'Step 2 of 2: Importing question {current} of {total}...',
                )
            final_results = db.add_questions(uid, parsed_results, progress_callback=import_progress)
            clear_read_caches()
            progress_bar.empty()
            stage.success('Step 2 of 2 complete: Import finished.')
            success_count = sum(1 for r in final_results if r['success'])
            fail_count = len(final_results) - success_count
            if fail_count == 0:
                st.success(f'{success_count} questions imported successfully.')
            else:
                st.warning(f"Import finished: {success_count} succeeded, {fail_count} failed.")
            df_data = []
            for r in final_results:
                df_data.append({
                    'Row': r['row_number'],
                    'Status': '✅ Success' if r['success'] else '❌ Failed',
                    'Error': r['error'] or '',
                    'Preview': (r.get('prompt') or '')[:80] + '...' if len(r.get('prompt') or '') > 80 else (r.get('prompt') or '')
                })
            st.dataframe(df_data, use_container_width=True)
            if st.button('Close'):
                st.rerun()
        except (QuestionImportError, ValueError) as exc:
            progress_bar.empty()
            if phase == 1:
                stage.error('Step 1 of 2: Validation failed. No questions were imported.')
            else:
                stage.error('Step 2 of 2: Import failed after validation completed.')
            st.error(str(exc))

    @st.dialog('Deleting Archived Questions')
    def wipe_archived_dialog(uid):
        progress_bar = st.progress(0, text='Preparing to delete...')
        def wipe_progress(current, total):
            progress_bar.progress(current / total if total > 0 else 1.0, text=f'Deleting question {current} of {total}...')
        try:
            db.wipe_archived_questions(uid, progress_callback=wipe_progress)
            clear_read_caches()
            progress_bar.empty()
            st.success('Archived questions and their related candidate records have been deleted.')
            if st.button('Close'):
                st.rerun()
        except ValueError as exc:
            progress_bar.empty()
            st.error(str(exc))

    @st.dialog('Confirm Question Bank Wipe')
    def wipe_question_bank_dialog(uid):
        st.warning(
            'This removes all unanswered questions and archives every question that has already been used in a candidate assessment.'
        )
        confirmed = st.checkbox('I understand that this action will clear the active Question Bank.')
        if st.button('Confirm Wipe Question Bank', type='primary', disabled=not confirmed):
            try:
                db.wipe_questions(uid)
                clear_read_caches()
                st.session_state['question_bank_wiped'] = True
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

st.markdown(f'''
<div class="logo-container">
    <img src="{cat_icon_data_url('C.A.T. Logo - Horizontal.jpg')}" alt="C.A.T. Logo">
</div>
<div class="company-details">
    <strong>QUALITY DEPARTMENT | C.A.T. INTERNATIONAL L.L.C.</strong><br>
    Ash Shulah, Dammam 34266, Saudi Arabia
</div>
''', unsafe_allow_html=True)
st.title('Competency Technical Assessment (CTA) Portal')
st.caption('Technical assessments · Multiple disciplines · Evidence-based grading')
if not cached_has_users():
    st.subheader('Initial administrator setup')
    st.info('Create the first administrator on a trusted local connection before exposing this app to the network.')
    account_form('bootstrap', bootstrap=True)
    st.stop()

if 'user' not in st.session_state:
    if timeout_message := st.session_state.pop('timeout_message', None):
        st.error(timeout_message)
    if st.session_state.pop('password_changed', False):
        st.success('Password changed. Sign in with your new password.')
    if st.session_state.pop('assessment_submitted', False):
        st.success('Assessment submitted successfully. You have been logged out.')
    login_container = st.empty()
    with login_container.container():
        with st.form('login'):
            username = st.text_input('Username')
            password = st.text_input('Password', type='password')
            if st.form_submit_button('Sign in', type='primary'):
                if time.time() < st.session_state.get('retry_after', 0):
                    st.error('Please wait a few seconds before trying again.')
                else:
                    user = db.authenticate(username, password)
                    if user:
                        login_token = secrets.token_urlsafe(32)
                        if not db.claim_login(user['id'], login_token):
                            st.error('This account is already logged in on another session.')
                            st.stop()
                        login_container.empty()
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.login_token = login_token
                        st.rerun()
                    else:
                        st.session_state.retry_after = time.time() + 3
                        st.error('Invalid username or password.')
    st.stop()

user = st.session_state.user
login_token = st.session_state.get('login_token')
if not login_token:
    st.session_state.clear()
    st.error('Your login session is invalid. Please sign in again.')
    st.stop()
now = time.time()
last_refresh = st.session_state.get('last_login_refresh', 0)
if now - last_refresh > 60:
    refreshed_user = db.refresh_login(user['id'], login_token)
    if not refreshed_user:
        st.session_state.clear()
        st.session_state.timeout_message = 'You were signed out after 15 minutes of inactivity. Please sign in again.'
        st.rerun()
    user = refreshed_user
    st.session_state.user = user
    st.session_state.last_login_refresh = now
st.sidebar.write(f"**{user['name']}**")
st.sidebar.caption(user['role'])
if user['role'] == 'Candidate':
    page = st.sidebar.radio('Navigation', ['Take assessment'])
    if page == 'Take assessment':
        st.subheader('Take an assessment')
        discipline = user.get('scheduled_discipline') or user.get('discipline', '')
        if not discipline:
            st.info('No discipline is assigned to this candidate.')
            st.stop()
        if discipline not in cached_disciplines():
            st.info('No assessments are currently available.')
            st.stop()
        bank = cached_questions(discipline)
        settings = cached_assessment_settings(user['id'])
        mcq_bank = [q for q in bank if q['q_type'] == 'mcq']
        reviewer_pools = {kind: [q for q in bank if q['q_type'] == kind] for kind in ('essay', 'oral', 'practical')}
        if len(mcq_bank) < settings['mcq'] or any(len(reviewer_pools[kind]) < settings[kind] for kind in reviewer_pools):
            st.error(f"This discipline needs {settings['mcq']} MCQ, {settings['essay']} Essay, {settings['oral']} Oral, and {settings['practical']} Practical Test questions.")
            st.stop()

        if st.session_state.get('assessment_discipline') != discipline:
            for key in list(st.session_state):
                if isinstance(key, str) and (key.startswith('assessment_') or key.startswith('answer_') or key in ('candidate_details', 'candidate_discipline_display', 'candidate_job_title')):
                    del st.session_state[key]
            st.session_state.assessment_discipline = discipline
            st.session_state.attempt_token = secrets.token_hex(24)

        details = st.session_state.get('candidate_details')
        if not details:
            st.subheader('Candidate Details')
            st.info(
                '**Candidate instructions**\n\n'
                '- Be presentable and maintain a professional appearance and conduct throughout the assessment, '
                'including the oral and practical portions.\n'
                '- You have 40 minutes to answer all Multiple Choice Questions. The countdown begins when you '
                'press the Start Multiple Choice Questions button.'
            )
            with st.form('candidate_details_form'):
                st.text_input('Discipline', value=discipline, disabled=True, key='candidate_discipline_display')
                designation = st.text_input('Job Title (Inspector, Supervisor, Technician...)', key='candidate_job_title')
                if st.form_submit_button('Start Multiple Choice Questions', type='primary'):
                    if not str(designation).strip():
                        st.error('Complete all candidate details before starting the assessment.')
                    else:
                        st.session_state.candidate_details = {
                            'name': user['name'], 'email': user.get('email', ''), 'designation': str(designation).strip(),
                            'iqama_no': user.get('iqama_no', ''), 'employee_no': user.get('employee_no', ''),
                            'exam_date': user.get('test_date') or date.today(), 'project_assignment': user.get('project_assignment', ''),
                        }
                        rng = secrets.SystemRandom()
                        try:
                            selected_mcqs = rng.sample(mcq_bank, settings['mcq'])
                            st.session_state.assessment_mcq_ids = [q['id'] for q in selected_mcqs]
                            st.session_state.assessment_essay_ids = [q['id'] for q in rng.sample(reviewer_pools['essay'], settings['essay'])]
                            st.session_state.assessment_reviewer_ids = [q['id'] for kind in ('oral', 'practical') for q in rng.sample(reviewer_pools[kind], settings[kind])]
                            st.session_state.assessment_mcq_options = {
                                q['id']: rng.sample(question_options(q), len(question_options(q)))
                                for q in selected_mcqs
                            }
                            started_at = time.time()
                            st.session_state.assessment_mcq_deadline = started_at + MCQ_TIME_LIMIT_SECONDS
                            st.session_state.assessment_essay_started_at = {}
                            st.session_state.assessment_essay_index = 0
                            st.session_state.assessment_counts = {kind: settings[kind] for kind in ('mcq', 'essay', 'oral', 'practical')}
                            st.session_state.assessment_phase = 'mcq'
                            st.rerun()
                        except (TypeError, ValueError, json.JSONDecodeError) as exc:
                            st.error(f'Unable to start the Competency Technical Assessment: {exc}')
            st.stop()

        question_map = {q['id']: q for q in bank}
        mcq_questions = [question_map[qid] for qid in st.session_state.assessment_mcq_ids]
        essay_questions = [question_map[qid] for qid in st.session_state.assessment_essay_ids if question_map[qid]['q_type'] == 'essay']
        responses = st.session_state.setdefault('assessment_responses', {})
        st.info(f"Complete {settings['mcq']} Multiple Choice Questions and {settings['essay']} Essay questions in the app. Oral ({settings['oral']}) and Practical Tests ({settings['practical']}) are completed and graded by a Reviewer.")
        if st.session_state.get('assessment_phase', 'mcq') == 'mcq':
            section = st.expander('Multiple Choice Questions', expanded=True)
            section.__enter__()
            st.subheader('Multiple Choice Questions')
            mcq_deadline = st.session_state.get('assessment_mcq_deadline', time.time() + MCQ_TIME_LIMIT_SECONDS)
            st.session_state.assessment_mcq_deadline = mcq_deadline
            countdown_timer('Time remaining for all Multiple Choice Questions', mcq_deadline, 'mcq')
            is_mcq_expired = time.time() > mcq_deadline
            if is_mcq_expired:
                st.warning('The 40-minute Multiple Choice time limit has expired. Selected answers will be saved as you continue.')
            with st.form('multiple_choice_questions'):
                page_responses = {}
                for number, question in enumerate(mcq_questions, 1):
                    page_responses[question['id']] = st.radio(
                        f"{number}. {question['question_text']}", st.session_state.assessment_mcq_options[question['id']], index=None,
                        key=f"answer_{question['id']}", disabled=is_mcq_expired)
                st.info('You have six minutes for each Essay question. The countdown begins when you press the Continue to Essay Questions button.')
                submit_label = 'Time expired: Proceed to Essay Questions' if is_mcq_expired else 'Continue to Essay Questions'
                if st.form_submit_button(submit_label, type='primary'):
                    if is_mcq_expired:
                        for q in mcq_questions:
                            ans = page_responses.get(q['id'])
                            responses[q['id']] = ans if isinstance(ans, str) and ans.strip() else '[Unanswered - time expired]'
                        st.session_state.assessment_phase = 'essay'
                        st.rerun()
                    elif any(not isinstance(answer, str) or not answer.strip() for answer in page_responses.values()):
                        st.error('Answer every Multiple Choice Question before continuing.')
                    else:
                        responses.update(page_responses)
                        st.session_state.assessment_phase = 'essay'
                        st.rerun()
            section.__exit__(None, None, None)
        else:
            section = st.expander('Essay Questions', expanded=True)
            section.__enter__()
            st.subheader('Essay Questions')
            st.info('Each Essay question has six minutes. Oral and Practical Tests are completed and graded by a Reviewer.')
            essay_index = st.session_state.setdefault('assessment_essay_index', 0)
            if essay_index >= len(essay_questions):
                st.success('All Essay questions are complete. Submit the assessment when ready.')
                if st.button('Submit assessment', type='primary'):
                    for q in essay_questions:
                        if q['id'] not in responses or not responses[q['id']].strip():
                            responses[q['id']] = '[No response submitted - time expired]'
                    try:
                        db.submit(
                            user['id'], discipline, responses, st.session_state.attempt_token,
                            st.session_state.candidate_details,
                            st.session_state.assessment_mcq_ids + st.session_state.assessment_essay_ids + st.session_state.assessment_reviewer_ids,
                            point_settings={kind: settings[f'{kind}_points'] for kind in ('mcq', 'essay', 'oral', 'practical')},
                            expected_counts=st.session_state.get('assessment_counts'))
                        clear_read_caches()
                        db.release_login(user['id'], st.session_state.login_token)
                        st.session_state.clear()
                        st.session_state.assessment_submitted = True
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                question = essay_questions[essay_index]
                started_at = st.session_state.setdefault('assessment_essay_started_at', {}).setdefault(question['id'], time.time())
                deadline = started_at + ESSAY_TIME_LIMIT_SECONDS
                expired = time.time() >= deadline
                st.caption(f"Essay Question {essay_index + 1} of {len(essay_questions)}")
                countdown_timer(f'Time remaining for Essay question {essay_index + 1} of {len(essay_questions)}', deadline, f'essay-{question["id"]}')
                if expired:
                    st.warning('Essay time expired. Click below to proceed to the next question.')
                with st.form(f'reviewer_scored_question_{question["id"]}'):
                    current_val = responses.get(question['id'], '')
                    answer = st.text_area(
                        f"{essay_index + 1}. Essay: {question['question_text']}",
                        value=current_val,
                        placeholder='Type your answer here...', height=220, max_chars=20000,
                        key=f"answer_{question['id']}", disabled=expired)
                    btn_label = 'Time expired: Go to next question' if expired else 'Save answer and go to next question'
                    if st.form_submit_button(btn_label, type='primary'):
                        if expired and not answer.strip():
                            responses[question['id']] = '[No response submitted - time expired]'
                        else:
                            responses[question['id']] = answer.strip()
                        st.session_state.assessment_essay_index = essay_index + 1
                        st.rerun()
            section.__exit__(None, None, None)
else:
    pages = ['Create Candidate Account', 'Create Candidate Schedules', 'Upcoming Candidate Schedules']
    pages += ['Assessment Settings', 'Review Assessments']
    if user['role'] == 'Admin':
        pages += ['Projects', 'Accounts']
    pages += ['Question Bank']
    page = st.sidebar.radio('Navigation', pages)
    if user['role'] in ('Admin', 'Reviewer'):
        with st.sidebar.expander('Change password'):
            def generate_new_password():
                generated = db.generate_password()
                st.session_state.change_new_password = generated
                st.session_state.change_confirm_password = generated
                st.session_state.change_generated_password = generated

            with st.form('change_password_form'):
                current_password = st.text_input('Current password', type='password')
                new_password = st.text_input('New password (at least 6 characters)', type='password', key='change_new_password')
                confirm_password = st.text_input('Confirm new password', type='password', key='change_confirm_password')
                st.form_submit_button('Generate random password', on_click=generate_new_password)
                if st.form_submit_button('Change password', type='primary'):
                    try:
                        if new_password != confirm_password:
                            raise ValueError('New passwords do not match.')
                        db.change_password(user['id'], current_password, new_password)
                        db.release_login(user['id'], login_token)
                        st.session_state.clear()
                        st.session_state.password_changed = True
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if generated := st.session_state.get('change_generated_password'):
                st.caption('Copy your generated password before saving:')
                st.code(generated, language=None)
    if st.sidebar.button('Sign out'):
        db.release_login(user['id'], login_token)
        st.session_state.clear()
        st.rerun()
    if page == 'Assessment Settings':
        st.subheader('Assessment Settings')
        st.caption('Set question counts and the maximum points awarded per question type. Changes apply to new assessments.')
        current = cached_assessment_settings(user['id'])
        with st.form('assessment_settings'):
            counts = {kind: st.number_input(label, min_value=1, max_value=100, value=current[kind], step=1) for kind, label in {
                'mcq': 'Multiple Choice Questions', 'essay': 'Essay Questions', 'oral': 'Oral Test Questions', 'practical': 'Practical Test Questions'
            }.items()}
            points = {kind: st.number_input(f'{label} maximum points per question', min_value=1.0, max_value=10.0, value=float(current[f'{kind}_points']), step=1.0) for kind, label in {
                'mcq': 'Multiple Choice', 'essay': 'Essay', 'oral': 'Oral Test', 'practical': 'Practical Test'
            }.items()}
            if st.form_submit_button('Save Assessment Settings', type='primary'):
                try:
                    db.update_assessment_settings(user['id'], {**{kind: int(value) for kind, value in counts.items()}, **{f'{kind}_points': float(value) for kind, value in points.items()}})
                    clear_read_caches()
                    st.success('Assessment Settings saved.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        if user['role'] == 'Admin':
            st.divider()
            st.subheader('Delete Individual Assessment')
            assessments = db.submissions(user['id'])
            if assessments:
                assessment_options = {r['id']: f"#{r['id']} · {r['candidate_name']} · {r['discipline']} · {r['status']}" for r in assessments}
                delete_id = st.selectbox('Assessment to delete', list(assessment_options), format_func=lambda value: assessment_options[value], key='delete_assessment_id')
                confirm_delete = st.checkbox('I understand this permanently deletes the selected assessment and its answers.', key='confirm_delete_assessment')
                if st.button('Delete Selected Assessment', type='secondary', disabled=not confirm_delete):
                    try:
                        db.delete_assessment(user['id'], delete_id)
                        clear_read_caches()
                        st.success('Assessment deleted permanently.')
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                st.info('No assessments are available to delete.')
            st.divider()
            with st.expander('Test email delivery'):
                st.caption('Send a test message to confirm SMTP settings before inviting candidates or reviewers.')
                test_email = st.text_input('Admin email address', value=user.get('email', ''), key='admin_test_email')
                if st.button('Send test email', type='primary'):
                    recipient = test_email.strip().lower()
                    if not recipient:
                        st.error('Enter an email address for the test message.')
                    elif hasattr(st, 'dialog'):
                        send_test_email_dialog(recipient, user.get('name') or 'Administrator')
                    else:
                        with st.status('Sending test email…'):
                            try:
                                send_test_email(recipient, user.get('name') or 'Administrator')
                                st.success(f'Test email sent to {recipient}.')
                            except (EmailDeliveryError, OSError, ValueError) as exc:
                                st.error(str(exc))
    elif page == 'Create Candidate Account':
        st.subheader('Create a candidate account')
        account_form('candidate_account', actor=user['id'], allowed_roles=['Candidate'])
    elif page == 'Create Candidate Schedules':
        st.subheader('Create Candidate Schedules')
        candidates = cached_candidate_accounts(user['id'])
        
        # Keep the filter controls to two per row so labels remain readable
        # on centered and narrower layouts.
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        with row1_col1: search_name = st.selectbox('Filter by Name', ['All'] + sorted({c['name'] for c in candidates}), key='schedule_filter_name')
        with row1_col2: search_discipline = st.selectbox('Filter by Discipline', ['All'] + sorted({c.get('scheduled_discipline') or c.get('discipline', '') for c in candidates if c.get('scheduled_discipline') or c.get('discipline')}), key='schedule_filter_discipline')
        with row2_col1: search_iqama = st.selectbox('Filter by Iqama', ['All'] + sorted({c['iqama_no'] for c in candidates if c.get('iqama_no')}), key='schedule_filter_iqama')
        with row2_col2: search_completion = st.selectbox('Assessment Completion Status', ['All', 'Complete', 'Incomplete'], key='schedule_filter_completion')
        
        filtered = candidates
        if search_name != 'All':
            filtered = [c for c in filtered if c['name'] == search_name]
        if search_discipline != 'All':
            filtered = [c for c in filtered if (c.get('scheduled_discipline') or c.get('discipline', '')) == search_discipline]
        if search_iqama != 'All':
            filtered = [c for c in filtered if c['iqama_no'] == search_iqama]
        if search_completion != 'All':
            filtered = [c for c in filtered if c.get('assessment_completion_status') == search_completion]
            
        if not filtered:
            st.info('No candidates found matching the filters.')
        else:
            options = {c['id']: f"{c['name']} - {c['discipline']} - {c['iqama_no']} - {c.get('assessment_completion_status', 'Incomplete')}" for c in filtered}
            selected_id = st.selectbox('Select Candidate', options=list(options.keys()), format_func=lambda x: options[x])
            
            if selected_id:
                candidate = next(c for c in filtered if c['id'] == selected_id)
                st.write(f"**Email:** {candidate['email']} | **Current Test Date:** {candidate['test_date']}")
                
                with st.form(f"schedule_{candidate['id']}"):
                    current_test_date = candidate['test_date']
                    # Leave an unscheduled candidate's date blank so a test
                    # schedule must be selected before saving.
                    schedule_date = st.date_input(
                        'Test date schedule *',
                        value=current_test_date,
                        min_value=min(current_test_date, date.today()) if current_test_date else date.today(),
                    )
                    disciplines = cached_disciplines()
                    discipline_options = ['Select discipline'] + disciplines
                    current_discipline = candidate.get('scheduled_discipline')
                    scheduled_discipline = st.selectbox(
                        'Candidate Discipline *',
                        discipline_options,
                        index=discipline_options.index(current_discipline) if current_discipline in discipline_options else 0,
                    )
                    projects = cached_projects(user['id'])
                    project_options = ['Select project assignment', 'Unassigned'] + [project for project in projects if project != 'Unassigned']
                    current_project = candidate.get('project_assignment')
                    project_assignment = st.selectbox(
                        'Project Assignment *',
                        project_options,
                        index=project_options.index(current_project) if current_project in project_options else 0,
                        help='Use Unassigned for new applicants taking the CTA before a project is assigned.',
                    )
                    if st.form_submit_button('Save Schedule', type='primary'):
                        try:
                            if not schedule_date:
                                raise ValueError('Candidate test date is required.')
                            if schedule_date < date.today():
                                raise ValueError('Test date must be today or a future date.')
                            if scheduled_discipline == 'Select discipline':
                                raise ValueError('Candidate Discipline is required.')
                            if project_assignment == 'Select project assignment':
                                raise ValueError('Project Assignment is required.')
                            db.update_candidate_schedule(user['id'], candidate['id'], schedule_date, project_assignment, scheduled_discipline)
                            clear_read_caches()
                            st.success('Schedule saved successfully.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                            
    elif page == 'Upcoming Candidate Schedules':
        st.subheader('Upcoming Candidate Schedules')
        candidates = cached_candidate_accounts(user['id'])
        
        today = date.today()
        scheduled_candidates = [c for c in candidates if c['test_date'] and c['test_date'] >= today]
        
        col1, col2, col3 = st.columns(3)
        with col1: search_name = st.selectbox('Filter by Name', ['All'] + sorted({str(c['name']).strip() for c in scheduled_candidates if c.get('name')}), key='upc_name')
        with col2: search_discipline = st.selectbox('Filter by Discipline', ['All'] + sorted({str(c.get('scheduled_discipline') or c.get('discipline', '')).strip() for c in scheduled_candidates if c.get('scheduled_discipline') or c.get('discipline')}), key='upc_disc')
        with col3: search_iqama = st.selectbox('Filter by Iqama', ['All'] + sorted({str(c['iqama_no']).strip() for c in scheduled_candidates if c.get('iqama_no')}), key='upc_iqama')
        
        upcoming = filter_upcoming_candidates(scheduled_candidates, search_name, search_discipline, search_iqama)
        st.caption(f'Showing {len(upcoming)} of {len(scheduled_candidates)} upcoming candidate(s).')
            
        if not upcoming:
            st.info('No upcoming schedules match the filters.')
        else:
            unsent_candidates = [c for c in upcoming if not c['invitation_sent_at'] and c.get('email')]
            if unsent_candidates:
                if st.button(f'Send Schedule & Credentials to All Pending ({len(unsent_candidates)})', type='primary', key='bulk_send_invites'):
                    success_count = 0
                    failed_count = 0
                    progress_text = st.empty()
                    for idx, c in enumerate(unsent_candidates, 1):
                        progress_text.caption(f"Sending {idx} of {len(unsent_candidates)}: {c['name']}...")
                        try:
                            temp_pw = db.generate_password()
                            db.set_candidate_temporary_password(user['id'], c['id'], temp_pw)
                            send_candidate_invitation(
                                c['email'], c['name'], c['username'],
                                temp_pw, c['test_date'], c.get('scheduled_discipline') or c['discipline'],
                            )
                            db.mark_invitation_sent(user['id'], c['id'])
                            success_count += 1
                        except Exception:
                            failed_count += 1
                    clear_read_caches()
                    progress_text.empty()
                    if failed_count:
                        st.warning(f"Sent {success_count} invitations; {failed_count} failed.")
                    else:
                        st.success(f"All {success_count} invitations sent successfully.")
                    st.rerun()
            for candidate in upcoming:
                with st.expander(f"{candidate['name']} - {candidate['discipline']} - {candidate['iqama_no']} - {candidate['test_date']}"):
                    st.write(f"**Email:** {candidate['email']}")
                    if candidate['invitation_sent_at']:
                        st.success('Invitation Sent')
                    else:
                        st.error('Invitation Not Sent')
                    
                    past = candidate.get('previous_schedules')
                    if past:
                        with st.popover("Past Schedules"):
                            for p in past:
                                st.caption(f"Date: {p['test_date']} (Re-scheduled: {p['scheduled_at'][:10]})")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if candidate['email'] and st.button('Send Schedule & Login Credentials', key=f"invite_{candidate['id']}", type='primary'):
                            try:
                                temporary_password = db.generate_password()
                                db.set_candidate_temporary_password(user['id'], candidate['id'], temporary_password)
                                send_candidate_invitation(
                                    candidate['email'], candidate['name'], candidate['username'],
                                    temporary_password, candidate['test_date'], candidate.get('scheduled_discipline') or candidate['discipline'],
                                )
                                db.mark_invitation_sent(user['id'], candidate['id'])
                                clear_read_caches()
                                st.success('Schedule and login credentials sent. The temporary password is now active.')
                                st.rerun()
                            except (EmailDeliveryError, OSError, ValueError) as exc:
                                st.error(str(exc))
                    with col2:
                        if user['role'] == 'Admin':
                            if st.button('Remove Schedule', key=f"remove_schedule_{candidate['id']}"):
                                try:
                                    db.remove_candidate_schedule(user['id'], candidate['id'])
                                    clear_read_caches()
                                    st.success('Schedule removed. Candidate account was kept.')
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))
    elif page == 'Projects':
        st.subheader('Projects')
        projects = cached_projects(user['id'])
        
        with st.form('add_project_form'):
            new_project = st.text_input('Project entry input box')
            if st.form_submit_button('Add Project'):
                try:
                    db.add_project(user['id'], new_project)
                    clear_read_caches()
                    st.success('Project added.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
                    
        st.write("Projects List box:")
        for p in projects:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(p)
            with col2:
                if st.button('Delete', key=f'del_proj_{p}'):
                    db.delete_project(user['id'], p)
                    clear_read_caches()
                    st.rerun()
        
        st.divider()
    elif page == 'Accounts':
        st.subheader('Accounts')
        if user['role'] == 'Admin':
            with st.expander('Manage Candidate Accounts'):
                candidates = cached_candidate_accounts(user['id'])
                col1, col2, col3 = st.columns(3)
                with col1:
                    filter_name = st.selectbox('Filter by Name', ['All'] + sorted({c['name'] for c in candidates}), key='accounts_filter_name')
                with col2:
                    filter_discipline = st.selectbox('Filter by Discipline', ['All'] + sorted({c.get('scheduled_discipline') or c.get('discipline', '') for c in candidates if c.get('scheduled_discipline') or c.get('discipline')}), key='accounts_filter_discipline')
                with col3:
                    filter_iqama = st.selectbox('Filter by Iqama', ['All'] + sorted({c['iqama_no'] for c in candidates if c.get('iqama_no')}), key='accounts_filter_iqama')
                filtered = candidates
                if filter_name != 'All': filtered = [c for c in filtered if c['name'] == filter_name]
                if filter_discipline != 'All': filtered = [c for c in filtered if (c.get('scheduled_discipline') or c.get('discipline', '')) == filter_discipline]
                if filter_iqama != 'All': filtered = [c for c in filtered if c['iqama_no'] == filter_iqama]
                if not filtered:
                    st.info('No candidate accounts match the filters.')
                else:
                    options = {c['id']: f"{c['name']} - {c['iqama_no']}" for c in filtered}
                    selected_id = st.selectbox('Select Candidate Account', list(options), format_func=lambda value: options[value], key='candidate_account_selection')
                    candidate = next(c for c in filtered if c['id'] == selected_id)
                    with st.form('edit_candidate_account'):
                        name = st.text_input('Full name *', value=candidate.get('name', ''))
                        email = st.text_input('Email *', value=candidate.get('email', ''))
                        iqama_no = st.text_input('Iqama No *', value=candidate.get('iqama_no', ''))
                        employee_no = st.text_input('Employee No', value=candidate.get('employee_no', ''))
                        mobile_no = st.text_input('Mobile No', value=candidate.get('mobile_no', ''))
                        if st.form_submit_button('Save Candidate Details', type='primary'):
                            try:
                                if not all(value.strip() for value in (name, email, iqama_no)): raise ValueError('Name, email, and Iqama No are required.')
                                db.update_candidate_details(user['id'], selected_id, name, email, iqama_no, employee_no, mobile_no)
                                clear_read_caches()
                                st.success('Candidate details updated successfully.')
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))
            st.divider()
        projects = cached_projects(user['id'])
        st.subheader('Create account')
        account_form('staff', actor=user['id'], allowed_roles=['Reviewer', 'Admin'])
        
        st.divider()
        st.subheader('Existing accounts')
        for staff in db.staff_accounts(user['id']):
            with st.expander(f"{staff['name']} ({staff['username']}) - {staff['role']}"):
                st.write(f"Email: {staff['email']}")
                
                if staff['role'] == 'Reviewer':
                    with st.form(f'update_reviewer_email_{staff["id"]}'):
                        reviewer_email = st.text_input(
                            'Reviewer email', value=staff.get('email', '')
                        )
                        if st.form_submit_button('Save Reviewer email'):
                            try:
                                db.update_reviewer_email(user['id'], staff['id'], reviewer_email)
                                st.success('Reviewer email saved.')
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))
                    with st.form(f'change_reviewer_password_{staff["id"]}'):
                        new_reviewer_password = st.text_input(
                            'New password (at least 6 characters)', type='password'
                        )
                        confirm_reviewer_password = st.text_input(
                            'Confirm new password', type='password'
                        )
                        if st.form_submit_button('Change Reviewer password'):
                            try:
                                if new_reviewer_password != confirm_reviewer_password:
                                    raise ValueError('Passwords do not match.')
                                db.set_reviewer_temporary_password(
                                    user['id'], staff['id'], new_reviewer_password
                                )
                                st.session_state[f'reviewer_password_{staff["id"]}'] = new_reviewer_password
                                st.success('Reviewer password changed. Send the credentials when ready.')
                            except ValueError as exc:
                                st.error(str(exc))
                    if st.button(
                        'Send Reviewer Credentials', key=f"email_reviewer_{staff['id']}"
                    ):
                        try:
                            if not staff['email']:
                                raise ValueError('This Reviewer does not have an email address.')
                            temporary_password = st.session_state.get(f'reviewer_password_{staff["id"]}')
                            if not temporary_password:
                                raise ValueError('Change the Reviewer password first, then send the credentials.')
                            send_reviewer_credentials(
                                staff['email'], staff['name'], staff['username'], temporary_password
                            )
                            st.session_state.pop(f'reviewer_password_{staff["id"]}', None)
                            st.success('Reviewer login credentials emailed.')
                        except (EmailDeliveryError, OSError, ValueError) as exc:
                            st.error(str(exc))
                    with st.form(f"assign_proj_{staff['id']}"):
                        assigned = st.multiselect('Assigned Projects list box', projects, default=staff.get('assigned_projects', []))
                        if st.form_submit_button('Save Assignments'):
                            try:
                                db.update_staff_projects(user['id'], staff['id'], assigned)
                                st.success('Assignments saved.')
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))
                                
                if staff['id'] != user['id']:
                    if st.button('Delete Account', key=f"del_staff_{staff['id']}", type='primary'):
                        try:
                            db.delete_user(user['id'], staff['id'])
                            clear_read_caches()
                            st.success('Staff account deleted.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
    elif page == 'Question Bank':
        st.subheader('Question Bank')
        st.caption('Add project-specific technical questions and rubrics before using this for hiring.')
        if st.session_state.pop('question_bank_wiped', False):
            st.success('Question Bank wiped. Unanswered questions were removed and answered questions were archived.')
        
        if user['role'] == 'Admin':
            with st.expander('Wipe Question Bank'):
                st.warning('This will delete all questions. Questions that have already been answered by candidates will be deactivated instead of deleted to preserve assessment records.')
                if st.button('Wipe Question Bank', type='primary'):
                    if hasattr(st, 'dialog'):
                        wipe_question_bank_dialog(user['id'])
                    else:
                        st.session_state['confirm_wipe_question_bank'] = True
                if st.session_state.get('confirm_wipe_question_bank'):
                    confirmed = st.checkbox(
                        'I understand that this action will clear the active Question Bank.',
                        key='confirm_wipe_question_bank_acknowledged',
                    )
                    if st.button('Confirm Wipe Question Bank', type='primary', disabled=not confirmed):
                        try:
                            db.wipe_questions(user['id'])
                            clear_read_caches()
                            st.session_state.pop('confirm_wipe_question_bank', None)
                            st.session_state['question_bank_wiped'] = True
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                        
                st.error('The following option is destructive. It will completely remove archived questions and delete the assessment records of any candidates who answered them.')
                if st.button('Wipe archived questions and candidate records'):
                    if hasattr(st, 'dialog'):
                        wipe_archived_dialog(user['id'])
                    else:
                        progress_bar = st.progress(0, text='Preparing to delete...')
                        def wipe_progress(current, total):
                            progress_bar.progress(current / total if total > 0 else 1.0, text=f'Deleting question {current} of {total}...')
                        try:
                            db.wipe_archived_questions(user['id'], progress_callback=wipe_progress)
                            clear_read_caches()
                            progress_bar.empty()
                            st.success('Archived questions and their related candidate records have been deleted.')
                            st.rerun()
                        except ValueError as exc:
                            progress_bar.empty()
                            st.error(str(exc))

        active_questions = cached_questions()
        template_column, export_column = st.columns(2)
        template_column.download_button(
            'Download Excel template', template_bytes(), 'qc-question-template.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True,
        )
        export_column.download_button(
            f'Export existing questions ({len(active_questions)})',
            export_questions_bytes(active_questions),
            'qc-existing-questions.xlsx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
            disabled=not active_questions,
        )
        with st.expander('Import questions from Excel'):
            upload = st.file_uploader('Excel workbook', type=['xlsx'], help='Use the downloaded template. Existing questions are not changed.')
            if upload is not None and st.button('Import questions', type='primary'):
                if hasattr(st, 'dialog'):
                    import_dialog(upload.getvalue(), user['id'])
                else:
                    stage = st.empty()
                    stage.info('Step 1 of 2: Validating the Excel workbook. No questions are being added yet.')
                    progress_bar = st.progress(0, text='Validating Excel workbook...')
                    phase = 1
                    try:
                        parsed_results = parse_questions(upload.getvalue())
                        valid_count = sum(1 for result in parsed_results if result['success'])
                        invalid_count = len(parsed_results) - valid_count
                        progress_bar.empty()
                        stage.info(
                            f'Step 2 of 2: Importing {valid_count} validated question(s) into the question bank. '
                            f'{invalid_count} row(s) will be reported as invalid.'
                        )
                        progress_bar = st.progress(0, text='Importing validated questions...')
                        phase = 2
                        def import_progress(current, total):
                            progress_bar.progress(
                                current / total if total > 0 else 1.0,
                                text=f'Step 2 of 2: Importing question {current} of {total}...',
                            )
                        final_results = db.add_questions(user['id'], parsed_results, progress_callback=import_progress)
                        clear_read_caches()
                        progress_bar.empty()
                        stage.success('Step 2 of 2 complete: Import finished.')
                        success_count = sum(1 for r in final_results if r['success'])
                        fail_count = len(final_results) - success_count
                        if fail_count == 0:
                            st.success(f'{success_count} questions imported successfully.')
                        else:
                            st.warning(f"Import finished: {success_count} succeeded, {fail_count} failed.")
                        df_data = []
                        for r in final_results:
                            df_data.append({
                                'Row': r['row_number'],
                                'Status': '✅ Success' if r['success'] else '❌ Failed',
                                'Error': r['error'] or '',
                                'Preview': (r.get('prompt') or '')[:80] + '...' if len(r.get('prompt') or '') > 80 else (r.get('prompt') or '')
                            })
                        st.dataframe(df_data, use_container_width=True)
                    except (QuestionImportError, ValueError) as exc:
                        progress_bar.empty()
                        if phase == 1:
                            stage.error('Step 1 of 2: Validation failed. No questions were imported.')
                        else:
                            stage.error('Step 2 of 2: Import failed after validation completed.')
                        st.error(str(exc))
        with st.expander('Add a question', expanded=True):
            kind = st.selectbox('Question type', ['mcq', 'essay', 'oral', 'practical'], format_func=lambda value: {
                'mcq': 'Multiple Choice Question', 'essay': 'Essay',
                'oral': 'Oral Test', 'practical': 'Practical Test'
            }[value])
            with st.form('new_question'):
                discipline = st.selectbox('Discipline', cached_disciplines())
                prompt = st.text_area('Question')
                options = st.text_area('Multiple Choice options (one per line)') if kind == 'mcq' else ''
                correct = st.text_input('Correct answer (exact option text)') if kind == 'mcq' else ''
                rubric = st.text_area('Scoring rubric') if kind in ('essay', 'oral', 'practical') else ''
                if st.form_submit_button('Add question'):
                    try:
                        db.add_question(user['id'], discipline, kind, prompt, options.splitlines(), correct.strip(), rubric)
                        clear_read_caches()
                        st.success('Question added.')
                    except ValueError as exc:
                        st.error(str(exc))
        if user['role'] == 'Admin':
            with st.expander('Auto-generate placeholder questions'):
                with st.form('autogenerate'):
                    auto_discipline = st.selectbox('Discipline', db.STARTER_DISCIPLINES)
                    auto_kind = st.selectbox('Question type', ['mcq', 'essay', 'oral', 'practical'], format_func=lambda value: {
                        'mcq': 'Multiple Choice Question', 'essay': 'Essay',
                        'oral': 'Oral Test', 'practical': 'Practical Test'
                    }[value])
                    auto_count = st.number_input('Number of questions', 1, 500, 5)
                    if st.form_submit_button('Generate'):
                        progress_bar = st.progress(0, text='Generating placeholder questions...')
                        def gen_progress(current, total):
                            progress_bar.progress(current / total if total > 0 else 1.0, text=f'Generating question {current} of {total}...')
                        try:
                            db.autogenerate_questions(user['id'], auto_discipline, auto_kind, int(auto_count), progress_callback=gen_progress)
                            clear_read_caches()
                            progress_bar.empty()
                            st.success(f'{auto_count} placeholder questions generated.')
                            # Use a short delay or just let the user see the success message
                        except ValueError as exc:
                            progress_bar.empty()
                            st.error(str(exc))
        st.divider()
        st.subheader('Browse questions')
        
        show_archived = st.checkbox('Show archived questions', value=False)
        all_questions = cached_questions(include_inactive=show_archived)
        all_disciplines = sorted(list(set(q['discipline'] for q in all_questions)))
        all_types = sorted(list(set(q['q_type'] for q in all_questions)))
        
        col1, col2, col3 = st.columns([1, 1, 1])
        filter_discipline = col1.selectbox('Filter by Discipline', ['All'] + all_disciplines)
        type_options = {
            'mcq': 'Multiple Choice Question', 'essay': 'Essay',
            'oral': 'Oral Test', 'practical': 'Practical Test'
        }
        filter_type = col2.selectbox('Filter by Question Type', ['All'] + all_types, format_func=lambda x: type_options.get(x, x))
        search_kw = col3.text_input('Search Question / Rubric', placeholder='Keyword...').strip().lower()
        
        filtered_questions = [
            q for q in all_questions 
            if (filter_discipline == 'All' or q['discipline'] == filter_discipline) and 
               (filter_type == 'All' or q['q_type'] == filter_type) and
               (not search_kw or search_kw in q['question_text'].lower() or search_kw in (q.get('rubric') or '').lower())
        ]
        
        if not filtered_questions:
            st.info('No questions match the selected filters.')
        else:
            page_size = 20
            total_pages = max(1, (len(filtered_questions) + page_size - 1) // page_size)
            if total_pages > 1:
                p_col1, p_col2 = st.columns([1, 3])
                with p_col1:
                    page_num = st.number_input('Page', min_value=1, max_value=total_pages, value=1, step=1, key='qb_page')
                with p_col2:
                    st.caption(f"Showing questions {(page_num-1)*page_size + 1} to {min(page_num*page_size, len(filtered_questions))} of {len(filtered_questions)}")
                page_questions = filtered_questions[(page_num - 1) * page_size : page_num * page_size]
            else:
                page_questions = filtered_questions
            
            for q in page_questions:
                with st.expander(f"#{q['id']} · {q['discipline']} · {type_options.get(q['q_type'], q['q_type'])} · {'Active' if q['active'] else 'Archived'}"):
                    st.write(q['question_text'])
                    if q['q_type'] == 'mcq':
                        options_list = json.loads(q['options']) if q.get('options') else []
                        for opt in options_list:
                            if opt == q['correct_answer']:
                                st.markdown(f"- ✅ **{opt}**")
                            else:
                                st.markdown(f"- ⬜ {opt}")
                    else:
                        st.write(q['rubric'])
                    if q.get('is_used'):
                        col_btn1, col_btn2 = st.columns([1, 4])
                        with col_btn1:
                            if st.button('Archive' if q['active'] else 'Restore', key=f"active_{q['id']}"):
                                db.set_active(user['id'], q['id'], not q['active'])
                                clear_read_caches()
                                st.rerun()
                        with col_btn2:
                            if not q['active']:
                                if st.button('Delete entirely (Removes candidate records)', key=f"hard_delete_{q['id']}", type='primary'):
                                    try:
                                        db.delete_question(user['id'], q['id'], force=True)
                                        st.rerun()
                                    except ValueError as exc:
                                        st.error(str(exc))
                    else:
                        if st.button('Delete', key=f"delete_{q['id']}"):
                            try:
                                db.delete_question(user['id'], q['id'])
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))
    else:
        st.subheader('Assessment review')
        rows = cached_submissions(user['id'])
        left, right = st.columns(2)
        left.metric('Pending review', sum(r['status'] == 'Pending Review' for r in rows))
        right.metric('Graded', sum(r['status'] == 'Graded' for r in rows))
        status = st.selectbox('Status', ['All', 'Pending Review', 'Graded'], index=1)
        rows = [r for r in rows if status == 'All' or r['status'] == status]
        if not rows:
            st.info('No assessments match this view.')
            st.stop()
        table = result_table(rows)
        st.markdown('''
        <style>
        [data-testid="stExpander"] details summary p { font-size: 1rem; }
        @media (max-width: 640px) {
            [data-testid="stExpander"] details summary p { font-size: .92rem; }
            [data-testid="stMarkdownContainer"] p { overflow-wrap: anywhere; }
        }
        </style>
        ''', unsafe_allow_html=True)
        for index, result_row in enumerate(table):
            summary = f"{result_row['Candidate']} · {result_row['Discipline']} · {result_row['Status']}"
            with st.expander(summary, expanded=False):
                for label, value in result_row.items():
                    st.markdown(f'**{label}:** {value if value != "" else "—"}')
        sid = st.selectbox('Assessment', [r['id'] for r in rows], format_func=lambda value: next(f"#{r['id']} · {r['candidate_name']} · {r['discipline']}" for r in rows if r['id'] == value))
        sub = next(r for r in rows if r['id'] == sid)
        try:
            result_pdf = cached_candidate_result_pdf(json.dumps(sub, default=str))
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                st.download_button('Download Candidate Result', result_pdf, 'candidate-result.pdf', 'application/pdf', use_container_width=True)
            with action_col2:
                if st.button('Email Result to Candidate', type='primary', use_container_width=True):
                    if not sub.get('email'):
                        st.error('This candidate does not have an email address.')
                    else:
                        try:
                            send_candidate_result(sub['email'], sub.get('candidate_name', 'Candidate'), result_pdf)
                            st.success(f'Result emailed to {sub["email"]}.')
                        except (EmailDeliveryError, OSError, ValueError) as exc:
                            st.error(str(exc))
        except (ImportError, OSError, ValueError) as exc:
            st.error(f'Unable to create the candidate result PDF. Install the reportlab package and retry. Details: {exc}')
        answers = db.answer_details(user['id'], sid)
        questionnaire = st.expander('Questionnaire', expanded=False)
        questionnaire.__enter__()
        with st.form(f'grading_{sid}'):
            scores = {}
            observed_responses = {}
            question_section = None
            question_section_type = None
            for a in answers:
                q = json.loads(a['snapshot'])
                if q['q_type'] != question_section_type:
                    if question_section is not None:
                        question_section.__exit__(None, None, None)
                    question_section_type = q['q_type']
                    section_title = {'mcq': 'Multiple Choice Questions', 'essay': 'Essay Questions', 'oral': 'Oral Test', 'practical': 'Practical Test'}.get(q['q_type'], 'Questions')
                    question_section = st.expander(section_title, expanded=sub['status'] != 'Graded')
                    question_section.__enter__()
                question_type = {
                    'mcq': 'Multiple Choice Question', 'essay': 'Essay', 'oral': 'Oral Test',
                    'practical': 'Practical Test',
                }.get(q['q_type'], q['q_type'])
                st.write(f"{question_type}: {q['question_text']}")
                if q['q_type'] in ('essay', 'oral', 'practical'):
                    if q['q_type'] == 'essay':
                        st.text_area('Candidate response', value=a['submitted_answer'], disabled=True,
                                     height=160, key=f"response_{a['id']}")
                    else:
                        observed_responses[a['id']] = st.text_area('Observed response', value=a['submitted_answer'], height=120,
                                                                    key=f"observed_response_{a['id']}", disabled=sub['status'] == 'Graded')
                    st.info(f"Scoring guidance: {q['rubric']}")
                    score_max = min(q['max_points'], 10)
                    scores[a['id']] = st.number_input(f"Points for answer #{a['id']} (max {int(score_max)})", min_value=0, max_value=int(score_max), value=min(int(a['awarded_score']), int(score_max)), step=1, disabled=sub['status'] == 'Graded')
                else:
                    st.caption(f"Correct answer: {q['correct_answer']} · Awarded: {a['awarded_score']:g}")
            if question_section is not None:
                question_section.__exit__(None, None, None)
            comments = st.text_area('Reviewer feedback', value=sub['reviewer_comments'] or '', disabled=sub['status'] == 'Graded')
            if st.form_submit_button('Finalize grade', disabled=sub['status'] == 'Graded', type='primary'):
                try:
                    db.grade(user['id'], sid, scores, comments, observed_responses)
                    clear_read_caches()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        questionnaire.__exit__(None, None, None)
        if sub['status'] == 'Graded':
            st.subheader('CTA Results')
            with st.expander('Results by Question Type', expanded=True):
                for kind, label in (('mcq', 'Multiple Choice'), ('essay', 'Essay'), ('oral', 'Oral Test'), ('practical', 'Practical Test')):
                    grade = db.category_result(sub, kind)
                    (st.success if grade.startswith('PASS') else st.error)(f'{label}: {grade}')
            with st.expander('Final Result', expanded=True):
                final_grade = db.result(sub)
                (st.success if final_grade.startswith('PASS') else st.error)(f'Final Grade: {final_grade}')
