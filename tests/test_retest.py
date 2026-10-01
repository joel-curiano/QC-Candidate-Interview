"""Retests must remove old results and allow only administrators."""
from datetime import date, timedelta

import pytest
import database as db


def test_retest_rejects_past_date_before_database_access(monkeypatch):
    def unexpected_connection():
        pytest.fail('Invalid retest dates must not access the database')
    monkeypatch.setattr(db, 'connection', unexpected_connection)
    with pytest.raises(ValueError, match='today or a future date'):
        db.issue_candidate_retest(1, 2, date.today() - timedelta(days=1))


def test_retest_deletes_results_and_draft(postgres_db):
    db.init_db()
    password = 'test-password-123'
    db.create_user('admin', 'Admin', password, bootstrap=True)
    admin = db.authenticate('admin', password)['id']
    db.create_user('candidate', 'Candidate', password, actor=admin,
                   email='candidate@example.com', iqama_no='1234567890', test_date=date.today())
    candidate = db.authenticate('candidate', password)['id']
    with db.connection() as c:
        submission = c.execute(
            "INSERT INTO submissions(user_id, token, max_possible_points, status) "
            "VALUES (%s, 'old-attempt', 1, 'Graded') RETURNING id", (candidate,)
        ).fetchone()['id']
        c.execute(
            "INSERT INTO answers(submission_id, question_id, submitted_answer, awarded_score, snapshot) "
            "VALUES (%s, 1, 'A', 1, '{}')", (submission,)
        )
    db.save_assessment_draft(candidate, {'attempt_token': 'old-attempt', 'assessment_mcq_deadline': 1})
    db.claim_login(candidate, 'old-session')
    with pytest.raises(ValueError):
        db.issue_candidate_retest(candidate, candidate, date.today())
    with db.connection() as c:
        assert c.execute('SELECT id FROM submissions WHERE id=%s', (submission,)).fetchone()
    new_date = date.today() + timedelta(days=1)
    db.issue_candidate_retest(admin, candidate, new_date)
    assert db.assessment_draft(candidate) is None
    assert not db.login_is_active(candidate, 'old-session')
    with db.connection() as c:
        assert not c.execute('SELECT id FROM submissions WHERE user_id=%s', (candidate,)).fetchall()
        assert not c.execute('SELECT id FROM answers WHERE submission_id=%s', (submission,)).fetchall()
        user = c.execute('SELECT test_date, invitation_sent_at FROM users WHERE id=%s', (candidate,)).fetchone()
        assert user['test_date'] == new_date
        assert user['invitation_sent_at'] is None
    with pytest.raises(ValueError, match='previous submission'):
        db.issue_candidate_retest(admin, candidate, new_date)
