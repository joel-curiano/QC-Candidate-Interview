"""Run with: streamlit run app.py"""
import csv
import io
import json
import secrets
import time
from datetime import date
import streamlit as st
import database as db
from email_service import EmailDeliveryError, send_candidate_invitation, send_reviewer_credentials, send_test_email
from question_import import QuestionImportError, parse_questions, template_bytes
from result_export import excel_bytes

st.set_page_config(page_title='QC Candidate Test Portal', page_icon='img/C.A.T. Emblem.jpg', layout='centered')
st.logo('img/C.A.T. Emblem.jpg')
st.markdown(
    '''<style>
    [data-testid="stSidebar"] {
        background-color: #d9dcde;
    }
    [data-testid="stMarkdownContainer"] h3 {
        color: #b51f2d !important;
    }
    </style>''',
    unsafe_allow_html=True,
)


def question_options(question):
    """Return MCQ options regardless of whether the database driver decoded JSON."""
    raw_options = question.get('options')
    if isinstance(raw_options, str):
        raw_options = json.loads(raw_options)
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError(f"Question {question.get('id', '')} has invalid Multiple Choice options.")
    return [str(option) for option in raw_options]


try:
    db.init_db()
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
        name = st.text_input('Full name')
        username = st.text_input('Username')
        
        is_candidate = allowed_roles == ['Candidate']
        account_email = st.text_input('Email') if is_candidate or actor is not None or bootstrap else ''
        
        discipline = ''
        iqama_no = ''
        employee_no = ''
        mobile_no = ''
        if is_candidate:
            disciplines = db.disciplines()
            discipline = st.selectbox('Discipline', disciplines) if disciplines else st.text_input('Discipline')
            iqama_no = st.text_input('Iqama No')
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
                if role == 'Reviewer' and not account_email.strip():
                    raise ValueError('Reviewer email is required so login credentials can be sent.')
                
                candidate_id = db.create_user(
                    username, name, password, role, actor, bootstrap, 
                    email=account_email, test_date=None,
                    discipline=discipline, iqama_no=iqama_no, 
                    employee_no=employee_no, mobile_no=mobile_no
                )
                if role == 'Reviewer':
                    try:
                        send_reviewer_credentials(account_email.strip().lower(), name.strip(), username.strip().lower(), password)
                        st.session_state.pop(generated_key, None)
                        st.success('Reviewer account created and login credentials emailed.')
                    except (EmailDeliveryError, OSError, ValueError) as exc:
                        st.warning(f'Account created, but the credentials email could not be sent: {exc}')
                else:
                    st.session_state.pop(generated_key, None)
                    st.success('Account created.')
                    if is_candidate:
                        st.session_state[f'{key}_reset'] = st.session_state.get(f'{key}_reset', 0) + 1
                        st.rerun()
                if bootstrap:
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    if not is_candidate and generated_key in st.session_state:
        st.caption('Copy this generated password and give it securely to the account owner:')
        st.code(st.session_state[generated_key], language=None)


def result_table(rows):
    return [{'Reference': r['id'], 'Candidate': r['candidate_name'], 'Candidate Email': r.get('email', ''),
             'Username': r.get('username', ''), 'Designation': r.get('designation', ''),
             'Iqama No': r.get('iqama_no', ''), 'Employee No': r.get('employee_no', ''),
             'Discipline': r['discipline'], 'Project Location': r.get('project_location', ''),
             'Scheduled Test Date': r.get('scheduled_test_date', ''), 'Exam Date': r.get('exam_date', ''),
             'Submitted (UTC)': r['created_at'] or 'Legacy record', 'Status': r['status'],
             'Multiple Choice Points': r['mcq_score'],
             'Essay Points': r.get('essay_only_score', 0) if r['status'] == 'Graded' else None,
             'Oral Points': r.get('oral_score', 0) if r['status'] == 'Graded' else None,
             'Practical Points': r.get('practical_score', 0) if r['status'] == 'Graded' else None,
             'Maximum Points': r['max_possible_points'], 'Result': db.result(r),
             'Reviewer Comments': r.get('reviewer_comments', ''), 'Graded (UTC)': r.get('graded_at', '')} for r in rows]

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
        progress_bar = st.progress(0, text='Parsing Excel file...')
        try:
            parsed_results = parse_questions(file_bytes)
            def import_progress(current, total):
                progress_bar.progress(current / total if total > 0 else 1.0, text=f'Importing question {current} of {total}...')
            final_results = db.add_questions(uid, parsed_results, progress_callback=import_progress)
            progress_bar.empty()
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
            st.error(str(exc))

    @st.dialog('Deleting Archived Questions')
    def wipe_archived_dialog(uid):
        progress_bar = st.progress(0, text='Preparing to delete...')
        def wipe_progress(current, total):
            progress_bar.progress(current / total if total > 0 else 1.0, text=f'Deleting question {current} of {total}...')
        try:
            db.wipe_archived_questions(uid, progress_callback=wipe_progress)
            progress_bar.empty()
            st.success('Archived questions and their related candidate records have been deleted.')
            if st.button('Close'):
                st.rerun()
        except ValueError as exc:
            progress_bar.empty()
            st.error(str(exc))

st.image('img/C.A.T. Logo - Horizontal.jpg', width=300)
st.title('QC Candidate Test Portal')
st.caption('Technical assessments · Multiple disciplines · Evidence-based grading')
if not db.has_users():
    st.subheader('Initial administrator setup')
    st.info('Create the first administrator on a trusted local connection before exposing this app to the network.')
    account_form('bootstrap', bootstrap=True)
    st.stop()

if 'user' not in st.session_state:
    if st.session_state.pop('password_changed', False):
        st.success('Password changed. Sign in with your new password.')
    with st.form('login'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        if st.form_submit_button('Sign in', type='primary'):
            if time.time() < st.session_state.get('retry_after', 0):
                st.error('Please wait a few seconds before trying again.')
            else:
                user = db.authenticate(username, password)
                if user:
                    st.session_state.clear()
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.session_state.retry_after = time.time() + 3
                    st.error('Invalid username or password.')
    st.stop()

user = st.session_state.user
with db.connection() as conn:
    user = db.require(conn, user['id'], ('Candidate', 'Reviewer', 'Admin'))
st.sidebar.write(f"**{user['name']}**")
st.sidebar.caption(user['role'])
with st.sidebar.expander('Change password'):
    def generate_new_password():
        generated = db.generate_password()
        st.session_state.change_new_password = generated
        st.session_state.change_confirm_password = generated
        st.session_state.change_generated_password = generated

    with st.form('change_password_form'):
        current_password = st.text_input('Current password', type='password')
        new_password = st.text_input(
            'New password (at least 6 characters)', type='password', key='change_new_password'
        )
        confirm_password = st.text_input(
            'Confirm new password', type='password', key='change_confirm_password'
        )
        st.form_submit_button('Generate random password', on_click=generate_new_password)
        if st.form_submit_button('Change password', type='primary'):
            try:
                if new_password != confirm_password:
                    raise ValueError('New passwords do not match.')
                db.change_password(user['id'], current_password, new_password)
                st.session_state.clear()
                st.session_state.password_changed = True
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    if generated := st.session_state.get('change_generated_password'):
        st.caption('Copy your generated password before saving:')
        st.code(generated, language=None)
if st.sidebar.button('Sign out'):
    st.session_state.clear()
    st.rerun()

if user['role'] == 'Candidate':
    if st.session_state.get('submitted_id'):
        st.success('This completes the online test. Next test is Oral and Practical Test.')
        if st.button('Sign out'):
            st.session_state.clear()
            st.rerun()
        st.stop()
    page = st.sidebar.radio('Navigation', ['Take assessment', 'My results'])
    if page == 'My results':
        st.subheader('My results')
        rows = db.submissions(user['id'])
        if not rows:
            st.info('Your submitted assessments will appear here.')
        else:
            st.dataframe(result_table(rows), hide_index=True, use_container_width=True)
            for r in rows:
                if r['status'] == 'Graded':
                    with st.expander(f"Assessment #{r['id']} · {db.result(r)}"):
                        st.write(r['reviewer_comments'] or 'No reviewer feedback provided.')
    else:
        st.subheader('Take an assessment')
        discipline = user.get('scheduled_discipline') or user.get('discipline', '')
        if not discipline:
            st.info('No discipline is assigned to this candidate.')
            st.stop()
        if discipline not in db.disciplines():
            st.info('No assessments are currently available.')
            st.stop()
        bank = db.questions(discipline)
        mcq_bank = [q for q in bank if q['q_type'] == 'mcq']
        reviewer_pools = {kind: [q for q in bank if q['q_type'] == kind] for kind in ('essay', 'oral', 'practical')}
        if len(mcq_bank) < 20 or any(len(pool) < 5 for pool in reviewer_pools.values()):
            st.error(f"This discipline needs at least 20 MCQ, 5 Essay, 5 Oral, and 5 Practical Test questions. It currently has {len(mcq_bank)} MCQ, {len(reviewer_pools['essay'])} Essay, {len(reviewer_pools['oral'])} Oral, and {len(reviewer_pools['practical'])} Practical Test questions.")
            st.stop()

        if st.session_state.get('assessment_discipline') != discipline:
            for key in list(st.session_state):
                if isinstance(key, str) and (key.startswith('assessment_') or key.startswith('answer_') or key == 'candidate_details'):
                    del st.session_state[key]
            st.session_state.assessment_discipline = discipline
            st.session_state.attempt_token = secrets.token_hex(24)

        details = st.session_state.get('candidate_details')
        if not details:
            st.subheader('Candidate Details')
            with st.form('candidate_details'):
                designation = st.text_input('Designation')
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
                            selected_mcqs = rng.sample(mcq_bank, 20)
                            st.session_state.assessment_mcq_ids = [q['id'] for q in selected_mcqs]
                            st.session_state.assessment_essay_ids = [q['id'] for kind in ('essay', 'oral', 'practical') for q in rng.sample(reviewer_pools[kind], 5)]
                            st.session_state.assessment_mcq_options = {
                                q['id']: rng.sample(question_options(q), len(question_options(q)))
                                for q in selected_mcqs
                            }
                            st.session_state.assessment_phase = 'mcq'
                            st.rerun()
                        except (TypeError, ValueError, json.JSONDecodeError) as exc:
                            st.error(f'Unable to start the Candidate Test: {exc}')
            st.stop()

        question_map = {q['id']: q for q in bank}
        mcq_questions = [question_map[qid] for qid in st.session_state.assessment_mcq_ids]
        essay_questions = [question_map[qid] for qid in st.session_state.assessment_essay_ids]
        responses = st.session_state.setdefault('assessment_responses', {})
        st.info('20 Multiple Choice Questions are followed by 5 Essay, 5 Oral, and 5 Practical Test questions. All answers are required.')
        if st.session_state.get('assessment_phase', 'mcq') == 'mcq':
            st.subheader('Multiple Choice Questions')
            with st.form('multiple_choice_questions'):
                page_responses = {}
                for number, question in enumerate(mcq_questions, 1):
                    page_responses[question['id']] = st.radio(
                        f"{number}. {question['question_text']}", st.session_state.assessment_mcq_options[question['id']], index=None,
                        key=f"answer_{question['id']}" )
                if st.form_submit_button('Continue to Essay, Oral, and Practical Tests', type='primary'):
                    if any(not isinstance(answer, str) or not answer.strip() for answer in page_responses.values()):
                        st.error('Answer every Multiple Choice Question before continuing.')
                    else:
                        responses.update(page_responses)
                        st.session_state.assessment_phase = 'essay'
                        st.rerun()
        else:
            st.subheader('Essay, Oral, and Practical Tests')
            st.info('Read each question and type your answer in the response box. Essay answers are reviewed and scored by a Reviewer.')
            with st.form('reviewer_scored_questions'):
                page_responses = {}
                for number, question in enumerate(essay_questions, 1):
                    question_type = {
                        'essay': 'Essay', 'oral': 'Oral Test', 'practical': 'Practical Test'
                    }.get(question['q_type'], 'Question')
                    page_responses[question['id']] = st.text_area(
                        f"{number}. {question_type}: {question['question_text']}",
                        placeholder='Type your answer here...', height=180, max_chars=20000,
                        key=f"answer_{question['id']}" )
                if st.form_submit_button('Submit assessment', type='primary'):
                    if any(not isinstance(answer, str) or not answer.strip() for answer in page_responses.values()):
                        st.error('Answer every Essay, Oral, and Practical question before submitting.')
                    else:
                        responses.update(page_responses)
                        try:
                            st.session_state.submitted_id = db.submit(
                                user['id'], discipline, responses, st.session_state.attempt_token,
                                st.session_state.candidate_details,
                                st.session_state.assessment_mcq_ids + st.session_state.assessment_essay_ids)
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
else:
    pages = ['Review Assessments', 'Create Candidate Account', 'Create Candidate Schedules', 'Upcoming Candidate Schedules']
    if user['role'] == 'Admin':
        pages += ['Projects', 'Accounts']
    pages += ['Question Bank']
    page = st.sidebar.radio('Navigation', pages)
    if page == 'Create Candidate Account':
        st.subheader('Create a candidate account')
        account_form('candidate_account', actor=user['id'], allowed_roles=['Candidate'])
    elif page == 'Create Candidate Schedules':
        st.subheader('Create Candidate Schedules')
        candidates = db.candidate_accounts(user['id'])
        
        col1, col2, col3 = st.columns(3)
        with col1: search_name = st.text_input('Filter by Name')
        with col2: search_discipline = st.text_input('Filter by Discipline')
        with col3: search_iqama = st.text_input('Filter by Iqama')
        
        filtered = candidates
        if search_name:
            filtered = [c for c in filtered if search_name.lower() in c['name'].lower()]
        if search_discipline:
            filtered = [c for c in filtered if search_discipline.lower() in c['discipline'].lower()]
        if search_iqama:
            filtered = [c for c in filtered if search_iqama.lower() in c['iqama_no'].lower()]
            
        if not filtered:
            st.info('No candidates found matching the filters.')
        else:
            options = {c['id']: f"{c['name']} - {c['discipline']} - {c['iqama_no']}" for c in filtered}
            selected_id = st.selectbox('Select Candidate', options=list(options.keys()), format_func=lambda x: options[x])
            
            if selected_id:
                candidate = next(c for c in filtered if c['id'] == selected_id)
                st.write(f"**Email:** {candidate['email']} | **Current Test Date:** {candidate['test_date']}")
                
                with st.form(f"schedule_{candidate['id']}"):
                    current_test_date = candidate['test_date'] or date.today()
                    # Keep legacy/past dates valid as the initial value, while
                    # requiring new selections to be today or later.
                    schedule_date = st.date_input(
                        'Test date schedule',
                        value=current_test_date,
                        min_value=min(current_test_date, date.today()),
                    )
                    disciplines = db.disciplines()
                    scheduled_discipline = st.selectbox('Candidate Discipline', disciplines, index=(disciplines.index(candidate.get('scheduled_discipline') or candidate.get('discipline')) if (candidate.get('scheduled_discipline') or candidate.get('discipline')) in disciplines else None))
                    projects = db.get_projects(user['id'])
                    project_assignment = st.selectbox('Project Assignment', projects, index=(projects.index(candidate.get('project_assignment')) if candidate.get('project_assignment') in projects else None)) if projects else st.text_input('Project Assignment', value=candidate.get('project_assignment', ''))
                    if st.form_submit_button('Save Schedule', type='primary'):
                        try:
                            if schedule_date < date.today():
                                raise ValueError('Test date must be today or a future date.')
                            db.update_candidate_schedule(user['id'], candidate['id'], schedule_date, project_assignment, scheduled_discipline)
                            st.success('Schedule saved successfully.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
                            
    elif page == 'Upcoming Candidate Schedules':
        st.subheader('Upcoming Candidate Schedules')
        candidates = db.candidate_accounts(user['id'])
        
        today = date.today()
        upcoming = [c for c in candidates if c['test_date'] and c['test_date'] >= today]
        
        col1, col2, col3 = st.columns(3)
        with col1: search_name = st.text_input('Filter by Name', key='upc_name')
        with col2: search_discipline = st.text_input('Filter by Discipline', key='upc_disc')
        with col3: search_iqama = st.text_input('Filter by Iqama', key='upc_iqama')
        
        if search_name:
            upcoming = [c for c in upcoming if search_name.lower() in c['name'].lower()]
        if search_discipline:
            upcoming = [c for c in upcoming if search_discipline.lower() in c['discipline'].lower()]
        if search_iqama:
            upcoming = [c for c in upcoming if search_iqama.lower() in c['iqama_no'].lower()]
            
        if not upcoming:
            st.info('No upcoming schedules match the filters.')
        else:
            for candidate in upcoming:
                with st.expander(f"{candidate['name']} - {candidate['discipline']} - {candidate['iqama_no']} - {candidate['test_date']}"):
                    st.write(f"**Email:** {candidate['email']}")
                    st.write('Invitation sent.' if candidate['invitation_sent_at'] else 'Invitation not sent.')
                    
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
                                st.success('Schedule and login credentials sent. The temporary password is now active.')
                                st.rerun()
                            except (EmailDeliveryError, OSError, ValueError) as exc:
                                st.error(str(exc))
                    with col2:
                        if user['role'] == 'Admin':
                            if st.button('Remove Schedule', key=f"remove_schedule_{candidate['id']}"):
                                try:
                                    db.remove_candidate_schedule(user['id'], candidate['id'])
                                    st.success('Schedule removed. Candidate account was kept.')
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))
    elif page == 'Projects':
        st.subheader('Projects')
        st.subheader('Test email delivery')
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
        st.divider()
        projects = db.get_projects(user['id'])
        
        with st.form('add_project_form'):
            new_project = st.text_input('Project entry input box')
            if st.form_submit_button('Add Project'):
                try:
                    db.add_project(user['id'], new_project)
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
                    st.rerun()
        
        st.divider()
    elif page == 'Accounts':
        st.subheader('Accounts')
        projects = db.get_projects(user['id'])
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
                            st.success('Staff account deleted.')
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
    elif page == 'Question Bank':
        st.subheader('Question Bank')
        st.caption('Add project-specific technical questions and rubrics before using this for hiring.')
        
        if user['role'] == 'Admin':
            with st.expander('Wipe Question Bank'):
                st.warning('This will delete all questions. Questions that have already been answered by candidates will be deactivated instead of deleted to preserve assessment records.')
                if st.button('Wipe Question Bank', type='primary'):
                    try:
                        db.wipe_questions(user['id'])
                        st.success('Question Bank wiped.')
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
                            progress_bar.empty()
                            st.success('Archived questions and their related candidate records have been deleted.')
                            st.rerun()
                        except ValueError as exc:
                            progress_bar.empty()
                            st.error(str(exc))

        st.download_button('Download Excel template', template_bytes(), 'qc-question-template.xlsx',
                           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        with st.expander('Import questions from Excel'):
            upload = st.file_uploader('Excel workbook', type=['xlsx'], help='Use the downloaded template. Existing questions are not changed.')
            if upload is not None and st.button('Import questions', type='primary'):
                if hasattr(st, 'dialog'):
                    import_dialog(upload.getvalue(), user['id'])
                else:
                    progress_bar = st.progress(0, text='Parsing Excel file...')
                    try:
                        parsed_results = parse_questions(upload.getvalue())
                        def import_progress(current, total):
                            progress_bar.progress(current / total if total > 0 else 1.0, text=f'Importing question {current} of {total}...')
                        final_results = db.add_questions(user['id'], parsed_results, progress_callback=import_progress)
                        progress_bar.empty()
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
                        st.error(str(exc))
        with st.expander('Add a question', expanded=True):
            kind = st.selectbox('Question type', ['mcq', 'essay', 'oral', 'practical'], format_func=lambda value: {
                'mcq': 'Multiple Choice Question', 'essay': 'Essay',
                'oral': 'Oral Test', 'practical': 'Practical Test'
            }[value])
            with st.form('new_question'):
                discipline = st.selectbox('Discipline', db.disciplines())
                prompt = st.text_area('Question')
                options = st.text_area('Multiple Choice options (one per line)') if kind == 'mcq' else ''
                correct = st.text_input('Correct answer (exact option text)') if kind == 'mcq' else ''
                rubric = st.text_area('Scoring rubric') if kind in ('essay', 'oral', 'practical') else ''
                points = st.number_input('Maximum points', 1, 100, 1 if kind == 'mcq' else 10, disabled=kind == 'mcq')
                if st.form_submit_button('Add question'):
                    try:
                        db.add_question(user['id'], discipline, kind, prompt, options.splitlines(), correct.strip(), rubric, points)
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
                            progress_bar.empty()
                            st.success(f'{auto_count} placeholder questions generated.')
                            # Use a short delay or just let the user see the success message
                        except ValueError as exc:
                            progress_bar.empty()
                            st.error(str(exc))
        st.divider()
        st.subheader('Browse questions')
        
        show_archived = st.checkbox('Show archived questions', value=False)
        all_questions = db.questions(include_inactive=show_archived)
        all_disciplines = sorted(list(set(q['discipline'] for q in all_questions)))
        all_types = sorted(list(set(q['q_type'] for q in all_questions)))
        
        col1, col2 = st.columns(2)
        filter_discipline = col1.selectbox('Filter by Discipline', ['All'] + all_disciplines)
        type_options = {
            'mcq': 'Multiple Choice Question', 'essay': 'Essay',
            'oral': 'Oral Test', 'practical': 'Practical Test'
        }
        filter_type = col2.selectbox('Filter by Question Type', ['All'] + all_types, format_func=lambda x: type_options.get(x, x))
        
        filtered_questions = [
            q for q in all_questions 
            if (filter_discipline == 'All' or q['discipline'] == filter_discipline) and 
               (filter_type == 'All' or q['q_type'] == filter_type)
        ]
        
        if not filtered_questions:
            st.info('No questions match the selected filters.')
        
        for q in filtered_questions:
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
        rows = db.submissions(user['id'])
        left, right = st.columns(2)
        left.metric('Pending review', sum(r['status'] == 'Pending Review' for r in rows))
        right.metric('Graded', sum(r['status'] == 'Graded' for r in rows))
        status = st.selectbox('Status', ['All', 'Pending Review', 'Graded'])
        rows = [r for r in rows if status == 'All' or r['status'] == status]
        if not rows:
            st.info('No assessments match this view.')
            st.stop()
        table = result_table(rows)
        st.dataframe(table, hide_index=True, use_container_width=True)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=table[0].keys())
        writer.writeheader()
        writer.writerows({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for k, v in r.items()} for r in table)
        st.download_button('Download results CSV', output.getvalue(), 'qc-results.csv', 'text/csv')
        st.download_button('Download CTA Record Log Excel', excel_bytes([dict(row, result=db.result(row)) for row in rows]), 'CTA Record Log.xlsx',
                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        sid = st.selectbox('Assessment', [r['id'] for r in rows], format_func=lambda value: next(f"#{r['id']} · {r['candidate_name']} · {r['discipline']}" for r in rows if r['id'] == value))
        sub = next(r for r in rows if r['id'] == sid)
        st.write(f"Multiple Choice score: {sub['mcq_score']:g} points · {db.result(sub)}")
        st.write({
            'Candidate': sub['candidate_name'],
            'Email': sub.get('email', ''),
            'Designation': sub.get('designation', ''),
            'Iqama No': sub.get('iqama_no', ''),
            'Employee No': sub.get('employee_no', ''),
            'Project Location': sub.get('project_location', ''),
            'Project Assignment': sub.get('project_assignment', sub.get('project_location', '')),
            'Scheduled Test Date': sub.get('scheduled_test_date', ''),
            'Exam Date': sub.get('exam_date', ''),
        })
        answers = db.answer_details(user['id'], sid)
        with st.form(f'grading_{sid}'):
            scores = {}
            for a in answers:
                q = json.loads(a['snapshot'])
                question_type = {
                    'mcq': 'Multiple Choice Question', 'essay': 'Essay', 'oral': 'Oral Test',
                    'practical': 'Practical Test',
                }.get(q['q_type'], q['q_type'])
                st.write(f"{question_type}: {q['question_text']}")
                st.text_area('Candidate response', value=a['submitted_answer'], disabled=True,
                             height=160, key=f"response_{a['id']}")
                if q['q_type'] in ('essay', 'oral', 'practical'):
                    st.info(q['rubric'])
                    scores[a['id']] = st.number_input(f"Points for answer #{a['id']} (max {q['max_points']})", min_value=0.0, max_value=float(q['max_points']), value=float(a['awarded_score']), step=0.5, disabled=sub['status'] == 'Graded')
                else:
                    st.caption(f"Correct answer: {q['correct_answer']} · Awarded: {a['awarded_score']:g}")
            comments = st.text_area('Reviewer feedback', value=sub['reviewer_comments'] or '', disabled=sub['status'] == 'Graded')
            if st.form_submit_button('Finalize grade', disabled=sub['status'] == 'Graded', type='primary'):
                try:
                    db.grade(user['id'], sid, scores, comments)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
