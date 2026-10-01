from contextlib import contextmanager
from datetime import date, timedelta
from unittest.mock import Mock

import pytest

import database as db


@pytest.mark.parametrize('role', ['Admin', 'Reviewer', 'Candidate'])
@pytest.mark.parametrize('candidate_role', [None, '', 'Inspector'])
def test_login_candidate_role(monkeypatch, role, candidate_role):
    user = dict.fromkeys(
        ('id', 'username', 'name', 'email', 'discipline', 'scheduled_discipline',
         'iqama_no', 'employee_no', 'project_assignment'), ''
    )
    user.update(role=role, test_date=date.today(), password=db.password_hash('test-password'))
    if candidate_role is not None:
        user['candidate_role'] = candidate_role
    connection = Mock()
    connection.execute.return_value.fetchone.return_value = user

    @contextmanager
    def connect():
        yield connection

    monkeypatch.setattr(db, 'connection', connect)
    authenticated = db.authenticate(' Staff ', 'test-password')
    assert authenticated['role'] == role
    assert 'password' not in authenticated
    if role == 'Candidate':
        assert authenticated['candidate_role'] == (candidate_role or '')
    else:
        assert 'candidate_role' not in authenticated
    assert db.authenticate('staff', 'wrong-password') is None
    user['test_date'] = date.today() - timedelta(days=1)
    assert bool(db.authenticate('staff', 'test-password')) == (role != 'Candidate')


@pytest.mark.parametrize('role', ['Admin', 'Reviewer'])
def test_staff_creation_rejects_candidate_role(role):
    with pytest.raises(ValueError, match='Only Candidate accounts'):
        db.create_user('staff', 'Staff', 'test-password', role=role, candidate_role='Inspector')
