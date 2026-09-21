from pathlib import Path
from datetime import date
from streamlit.testing.v1 import AppTest
import database as db

APP = str(Path(__file__).parents[1] / 'app.py')
PASSWORD = 'test-password-123'


def test_first_run_setup(postgres_db):
    at = AppTest.from_file(APP, default_timeout=15).run()
    assert not at.exception
    for field, value in zip(at.text_input, ['Admin', 'admin', PASSWORD, PASSWORD]):
        field.input(value)
    at.button[0].click().run()
    assert not at.exception
    assert db.authenticate('admin', PASSWORD)['role'] == 'Admin'


def test_candidate_and_reviewer_flow(postgres_db):
    db.init_db()
    db.create_user('admin', 'Admin', PASSWORD, bootstrap=True)
    admin = db.authenticate('admin', PASSWORD)
    db.create_user('candidate', 'Candidate', PASSWORD, actor=admin['id'], email='candidate@example.com', test_date=date.today(), discipline='Welding QC', iqama_no='1234567890', employee_no='EMP-1')
    mcq_difficulties = ['easy'] * 6 + ['moderate'] * 10 + ['difficult'] * 4
    for index, difficulty in enumerate(mcq_difficulties):
        db.add_question(
            admin['id'], 'Welding QC', 'mcq', f'Additional choice {index}', ['A', 'B'], 'A', '',
            difficulty=difficulty,
        )
    essay_difficulties = ['easy'] + ['moderate'] * 3 + ['difficult']
    for index, difficulty in enumerate(essay_difficulties):
        db.add_question(
            admin['id'], 'Welding QC', 'essay', f'Additional essay {index}', [], '', 'Award for evidence.',
            difficulty=difficulty,
        )
    oral_practical_difficulties = ['easy'] * 2 + ['moderate'] * 3 + ['difficult']
    for index, difficulty in enumerate(oral_practical_difficulties):
        db.add_question(
            admin['id'], 'Welding QC', 'oral_practical', f'Additional oral-practical {index}', [], '',
            'Award for evidence.', difficulty=difficulty,
        )
    candidate = db.authenticate('candidate', PASSWORD)
    at = AppTest.from_file(APP, default_timeout=15).run()
    at.text_input[0].input('candidate')
    at.text_input[1].input(PASSWORD)
    next(b for b in at.button if b.label == 'Sign in').click().run()
    assert not at.exception
    next(widget for widget in at.selectbox if widget.label == 'Job Title').set_value('Inspector')
    next(b for b in at.button if b.label == 'Start Multiple Choice Questions').click().run()
    for radio in at.radio:
        if radio.label != 'Navigation':
            radio.set_value(radio.options[0])
    next(b for b in at.button if b.label == 'Continue to Essay Questions').click().run()
    for area in at.text_area:
        area.input('Verify criteria, collect inspection evidence, report nonconformance and verify closure.')
    next(b for b in at.button if b.label == 'Submit assessment').click().run()
    assert not at.exception
    assert len(db.submissions(candidate['id'])) == 1
    reviewer = AppTest.from_file(APP, default_timeout=15)
    reviewer.session_state['user'] = admin
    reviewer.run()
    assert not reviewer.exception
    for score in reviewer.number_input:
        score.set_value(20.0)
    next(t for t in reviewer.text_area if t.label == 'Reviewer feedback').input('Complete response.')
    next(b for b in reviewer.button if b.label == 'Finalize grade').click().run()
    assert not reviewer.exception
    assert db.result(db.submissions(candidate['id'])[0]) == 'PASS (100.0%)'
    next(r for r in at.radio if r.label == 'Navigation').set_value('My results').run()
    assert not at.exception
    assert at.dataframe
    next(r for r in reviewer.radio if r.label == 'Navigation').set_value('Question bank').run()
    assert not reviewer.exception
    next(r for r in reviewer.radio if r.label == 'Navigation').set_value('Create staff account').run()
    assert not reviewer.exception
