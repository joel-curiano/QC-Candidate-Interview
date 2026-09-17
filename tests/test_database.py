import json
from datetime import date, timedelta
import pytest
import database as db

PASSWORD = 'test-password-123'

@pytest.fixture
def accounts(postgres_db):
    db.init_db()
    db.create_user('admin', 'Administrator', PASSWORD, bootstrap=True)
    admin = db.authenticate('admin', PASSWORD)['id']
    db.create_user('reviewer', 'Reviewer', PASSWORD, 'Reviewer', actor=admin, email='reviewer@example.com')
    db.create_user('alice', 'Alice', PASSWORD, actor=admin, email='alice@example.com', test_date=date.today())
    db.create_user('bob', 'Bob', PASSWORD, actor=admin, email='bob@example.com', test_date=date.today())
    return {name: db.authenticate(name, PASSWORD)['id'] for name in ('admin', 'reviewer', 'alice', 'bob')}

def attempt(accounts, token='attempt'):
    qs = db.questions('Welding QC')
    responses = {q['id']: q['correct_answer'] if q['q_type'] == 'mcq' else 'Inspection evidence and closure.' for q in qs}
    sid = db.submit(accounts['alice'], 'Welding QC', responses, token)
    return sid, responses

def test_auth_and_roles(accounts):
    assert db.authenticate('ALICE', PASSWORD)['role'] == 'Candidate'
    assert db.authenticate('alice', 'incorrect') is None
    with pytest.raises(ValueError):
        db.create_user('evil', 'Evil', PASSWORD, 'Admin')
    with pytest.raises(ValueError):
        db.create_user('second', 'Second', PASSWORD, bootstrap=True)
    with pytest.raises(ValueError):
        db.set_active(accounts['alice'], 1, False)
    with pytest.raises(ValueError):
        db.create_user('staff', 'Staff', PASSWORD, 'Reviewer', actor=accounts['reviewer'])
    with db.connection() as c:
        assert c.execute("SELECT password FROM users WHERE username='alice'").fetchone()['password'] != PASSWORD
    db.add_question(accounts['reviewer'], 'E&I QC', 'mcq', 'Choose E&I evidence', ['A', 'B'], 'A', '')
    assert 'E&I QC' in db.disciplines()
    assert 'Mechanical QC' in db.disciplines()
    assert 'Communications QC' in db.disciplines()

def test_candidate_login_requires_scheduled_date(accounts):
    db.create_user('future', 'Future Candidate', PASSWORD, actor=accounts['admin'], email='future@example.com', test_date=date.today() + timedelta(days=1))
    assert db.authenticate('future', PASSWORD) is None

def test_change_password_requires_current_password(accounts):
    with pytest.raises(ValueError, match='Current password is incorrect'):
        db.change_password(accounts['alice'], 'wrong-password', 'new-password')
    with pytest.raises(ValueError, match='at least 6 characters'):
        db.change_password(accounts['alice'], PASSWORD, 'short')
    with pytest.raises(ValueError, match='different'):
        db.change_password(accounts['alice'], PASSWORD, PASSWORD)

    db.change_password(accounts['alice'], PASSWORD, 'new-password')

    assert db.authenticate('alice', PASSWORD) is None
    assert db.authenticate('alice', 'new-password')['id'] == accounts['alice']

    temporary_password = db.generate_password()
    db.set_candidate_temporary_password(accounts['admin'], accounts['alice'], temporary_password)
    assert db.authenticate('alice', 'new-password') is None
    assert db.authenticate('alice', temporary_password)['id'] == accounts['alice']
    with pytest.raises(ValueError):
        db.set_candidate_temporary_password(accounts['alice'], accounts['bob'], temporary_password)

    reviewer_password = db.generate_password()
    db.set_reviewer_temporary_password(accounts['admin'], accounts['reviewer'], reviewer_password)
    assert db.authenticate('reviewer', PASSWORD) is None
    assert db.authenticate('reviewer', reviewer_password)['id'] == accounts['reviewer']
    with pytest.raises(ValueError):
        db.set_reviewer_temporary_password(accounts['reviewer'], accounts['reviewer'], reviewer_password)


def test_generated_password_meets_requirements():
    password = db.generate_password()
    assert len(password) == 12
    assert any(char.islower() for char in password)
    assert any(char.isupper() for char in password)
    assert any(char.isdigit() for char in password)
    assert any(not char.isalnum() for char in password)
    assert password != db.generate_password()


def test_scoring_and_isolation(accounts):
    sid, responses = attempt(accounts)
    assert db.submit(accounts['alice'], 'Welding QC', responses, 'attempt') == sid
    assert db.submissions(accounts['bob']) == []
    sub = db.submissions(accounts['alice'])[0]
    assert sub['mcq_score'] == 10
    assert db.result(sub) == 'Pending Review'
    with pytest.raises(ValueError):
        db.answer_details(accounts['alice'], sid)
    answers = db.answer_details(accounts['reviewer'], sid)
    essay = next(a for a in answers if json.loads(a['snapshot'])['q_type'] == 'essay')
    with pytest.raises(ValueError):
        db.grade(accounts['alice'], sid, {essay['id']: 20}, '')
    for bad in (-1, 21, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            db.grade(accounts['reviewer'], sid, {essay['id']: bad}, '')
    with pytest.raises(ValueError):
        db.grade(accounts['reviewer'], sid, {}, '')
    db.grade(accounts['reviewer'], sid, {essay['id']: 11}, 'Meets threshold')
    assert db.result(db.submissions(accounts['alice'])[0]) == 'PASS (70.0%)'
    with pytest.raises(ValueError):
        db.grade(accounts['admin'], sid, {essay['id']: 0}, '')

def test_validation_and_snapshots(accounts):
    qs = db.questions('Welding QC')
    with pytest.raises(ValueError):
        db.submit(accounts['alice'], 'Welding QC', {q['id']: '' for q in qs}, 'blank')
    assert db.submissions(accounts['alice']) == []
    sid, responses = attempt(accounts)
    db.set_active(accounts['admin'], qs[0]['id'], False)
    with pytest.raises(ValueError):
        db.submit(accounts['alice'], 'Welding QC', responses, 'stale')
    assert len(db.answer_details(accounts['admin'], sid)) == 2
    assert json.loads(db.answer_details(accounts['admin'], sid)[0]['snapshot'])['max_points'] == 10

def test_mcq_only_and_wrong_answer(accounts):
    db.add_question(accounts['admin'], 'Test', 'mcq', 'Choose A', ['A', 'B'], 'A', '')
    q = db.questions('Test')[0]
    sid = db.submit(accounts['alice'], 'Test', {q['id']: 'B'}, 'wrong')
    assert db.result(db.submissions(accounts['alice'])[0]) == 'FAIL (0.0%)'
    assert db.answer_details(accounts['admin'], sid)[0]['awarded_score'] == 0

def test_concurrent_duplicate_submission(accounts):
    from concurrent.futures import ThreadPoolExecutor
    qs = db.questions('Welding QC')
    responses = {q['id']: q['correct_answer'] if q['q_type'] == 'mcq' else 'Essay' for q in qs}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(db.submit, accounts['alice'], 'Welding QC', responses, 'same-token') for _ in range(2)]
        ids = [future.result() for future in futures]
    assert ids[0] == ids[1]
    assert len(db.submissions(accounts['alice'])) == 1


def test_concurrent_review_and_transaction_rollback(accounts):
    from concurrent.futures import ThreadPoolExecutor
    sid, _ = attempt(accounts)
    essays = [a for a in db.answer_details(accounts['admin'], sid) if json.loads(a['snapshot'])['q_type'] == 'essay']
    scores = {a['id']: 15 for a in essays}

    def finalize():
        try:
            db.grade(accounts['reviewer'], sid, scores, 'Reviewed')
            return 'saved'
        except ValueError:
            return 'already graded'

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(finalize) for _ in range(2)]
        assert sorted(f.result() for f in futures) == ['already graded', 'saved']

    db.add_question(accounts['admin'], 'Welding QC', 'essay', 'Second essay', [], '', 'Rubric')
    sid, _ = attempt(accounts, 'rollback')
    essays = [a for a in db.answer_details(accounts['admin'], sid) if json.loads(a['snapshot'])['q_type'] == 'essay']
    with pytest.raises(ValueError):
        db.grade(accounts['reviewer'], sid, {essays[0]['id']: 10, essays[1]['id']: 11}, '')
    assert all(a['awarded_score'] == 0 for a in db.answer_details(accounts['admin'], sid) if json.loads(a['snapshot'])['q_type'] == 'essay')
    assert db.submissions(accounts['alice'])[0]['status'] == 'Pending Review'


@pytest.mark.parametrize('existing_bank', [False, True])
def test_civil_qc_seed_is_idempotent(postgres_db, existing_bank):
    if existing_bank:
        with db.connection() as c:
            c.execute("INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,max_points) VALUES ('Other QC','mcq','Existing question','[\"A\",\"B\"]','A',10)")
    db.init_db()
    civil = db.questions('Civil QC')
    assert {q['q_type'] for q in civil} == {'mcq', 'essay'}
    assert len(civil) == 2
    ids = {q['id'] for q in civil}
    db.init_db()
    assert {q['id'] for q in db.questions('Civil QC')} == ids
    with db.connection() as c:
        c.execute("UPDATE questions SET active=0 WHERE discipline='Civil QC'")
    db.init_db()
    assert db.questions('Civil QC') == []
    assert {q['id'] for q in db.questions('Civil QC', include_inactive=True)} == ids
    if existing_bank:
        assert len(db.questions('Other QC')) == 1


def test_submission_with_timed_out_essay(accounts):
    qs = db.questions('Welding QC')
    mcq = next(q for q in qs if q['q_type'] == 'mcq')
    essay = next(q for q in qs if q['q_type'] == 'essay')
    responses = {
        mcq['id']: 'Shielding gas and clean bevel',
        essay['id']: '[No response submitted - time expired]',
    }
    sid = db.submit(accounts['alice'], 'Welding QC', responses, 'timeout-attempt')
    assert sid > 0
    answers = db.answer_details(accounts['admin'], sid)
    essay_ans = next(a for a in answers if a['question_id'] == essay['id'])
    assert essay_ans['submitted_answer'] == '[No response submitted - time expired]'
