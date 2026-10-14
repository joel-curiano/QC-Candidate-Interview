import pytest
from streamlit.testing.v1 import AppTest
import database as db

APP = 'pages/3_Review_Assessments.py'
PASSWORD = 'test-password-123'

def test_reviewer_access(postgres_db):
    db.init_db()
    db.create_user('admin', 'Admin', PASSWORD, bootstrap=True)
    admin = db.authenticate('admin', PASSWORD)
    db.create_user('reviewer', 'Reviewer', PASSWORD, 'Reviewer', actor=admin['id'], email='rev@test.com')
    reviewer = db.authenticate('reviewer', PASSWORD)
    
    # Need to simulate a login token in DB too
    with db.connection() as c:
        c.execute("UPDATE users SET current_login_token='token123' WHERE id=%s", (reviewer['id'],))
        
    at = AppTest.from_file(APP, default_timeout=15)
    at.session_state['user'] = reviewer
    at.session_state['login_token'] = 'token123'
    at.run()
    
    if at.exception:
        print("EXCEPTION:", at.exception)
        assert False
    else:
        print("SUCCESS")


def test_questionnaire_groups_interleaved_question_types(postgres_db):
    db.init_db()
    db.create_user('admin', 'Admin', PASSWORD, bootstrap=True)
    admin = db.authenticate('admin', PASSWORD)
    db.create_user('reviewer', 'Reviewer', PASSWORD, 'Reviewer', actor=admin['id'], email='rev@test.com')
    reviewer = db.authenticate('reviewer', PASSWORD)
    db.create_user(
        'candidate', 'Candidate One', PASSWORD, actor=admin['id'],
        email='cand@test.com', discipline='Telecom QC', iqama_no='1234567890', employee_no='EMP-10',
    )
    candidate = db.authenticate('candidate', PASSWORD)

    # Insert questions in interleaved order: mcq, essay, oral_practical, essay, oral_practical
    db.add_question(admin['id'], 'Telecom QC', 'mcq', 'Interleaved MCQ 1', ['Option A', 'Option B'], 'Option A', '')
    db.add_question(admin['id'], 'Telecom QC', 'essay', 'Interleaved Essay 1', [], '', 'Rubric E1')
    db.add_question(admin['id'], 'Telecom QC', 'oral_practical', 'Interleaved Oral 1', [], '', 'Rubric O1')
    db.add_question(admin['id'], 'Telecom QC', 'essay', 'Interleaved Essay 2', [], '', 'Rubric E2')
    db.add_question(admin['id'], 'Telecom QC', 'oral_practical', 'Interleaved Oral 2', [], '', 'Rubric O2')

    custom_qs = [
        q for q in db.questions('Telecom QC')
        if q['question_text'].startswith('Interleaved ')
    ]
    responses = {
        q['id']: ('Option A' if q['q_type'] == 'mcq' else 'Detailed technical response.')
        for q in custom_qs
        if q['q_type'] != 'oral_practical'
    }
    sid = db.submit(
        candidate['id'],
        'Telecom QC',
        responses,
        'interleaved-token-1',
        {'name': 'Candidate One', 'designation': 'Inspector'},
        question_ids=[q['id'] for q in custom_qs],
        expected_counts={'mcq': 1, 'essay': 2, 'oral_practical': 2},
    )

    # Verify db.answer_details returns answers grouped by canonical QUESTION_TYPES
    details = db.answer_details(reviewer['id'], sid)
    q_types = [db.json.loads(a['snapshot'])['q_type'] for a in details]
    assert q_types == ['mcq', 'essay', 'essay', 'oral_practical', 'oral_practical']

    # Verify Review Assessments page renders exactly one expander per question type
    db.claim_login(reviewer['id'], 'token-group-test')
    at = AppTest.from_file(APP, default_timeout=15)
    at.session_state['user'] = reviewer
    at.session_state['login_token'] = 'token-group-test'
    at.run()
    assert not at.exception

    expander_labels = [exp.label for exp in at.expander]
    assert expander_labels.count('Multiple Choice Questions') == 1
    assert expander_labels.count('Essay Questions') == 1
    assert expander_labels.count('Oral-Practical Questions') == 1


def test_order_answers_by_question_type_groups_interleaved_rows():
    interleaved_rows = [
        {'id': 10, 'snapshot': '{"q_type": "mcq", "question_text": "M1"}'},
        {'id': 11, 'snapshot': '{"q_type": "essay", "question_text": "E1"}'},
        {'id': 12, 'snapshot': '{"q_type": "oral_practical", "question_text": "O1"}'},
        {'id': 13, 'snapshot': '{"q_type": "essay", "question_text": "E2"}'},
        {'id': 14, 'snapshot': '{"q_type": "oral_practical", "question_text": "O2"}'},
        {'id': 15, 'snapshot': '{"q_type": "mcq", "question_text": "M2"}'},
    ]
    ordered = db._order_answers_by_question_type(interleaved_rows)
    assert [r['id'] for r in ordered] == [10, 15, 11, 13, 12, 14]
    assert [db.json.loads(r['snapshot'])['q_type'] for r in ordered] == [
        'mcq', 'mcq', 'essay', 'essay', 'oral_practical', 'oral_practical'
    ]


