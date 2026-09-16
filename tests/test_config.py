"""Checks that do not need a running PostgreSQL server."""
from pathlib import Path
from datetime import date
from unittest.mock import MagicMock
import pytest
import psycopg
import streamlit as st
from streamlit.testing.v1 import AppTest
import database as db


def test_environment_precedes_secrets(monkeypatch):
    monkeypatch.setenv('SUPABASE_DB_URL', 'postgresql://env-value')
    monkeypatch.setattr(st, 'secrets', {'SUPABASE_DB_URL': 'postgresql://secret-value'})
    assert db.database_url() == 'postgresql://env-value'


def test_streamlit_secrets_and_missing_config(monkeypatch):
    monkeypatch.delenv('SUPABASE_DB_URL', raising=False)
    monkeypatch.setattr(st, 'secrets', {'SUPABASE_DB_URL': 'postgresql://secret-value'})
    assert db.database_url() == 'postgresql://secret-value'
    monkeypatch.setattr(st, 'secrets', {})
    with pytest.raises(db.DatabaseError, match='Set SUPABASE_DB_URL'):
        db.database_url()
    at = AppTest.from_file(str(Path(__file__).parents[1] / 'app.py')).run()
    assert not at.exception
    assert 'SUPABASE_DB_URL' in at.error[0].value


def test_connection_enforces_tls_and_transaction(monkeypatch):
    monkeypatch.setenv('SUPABASE_DB_URL', 'postgresql://placeholder')
    connect = MagicMock()
    monkeypatch.setattr(db.psycopg, 'connect', connect)
    with db.connection() as c:
        assert c is connect.return_value.__enter__.return_value
    assert connect.call_args.kwargs['sslmode'] == 'require'
    assert connect.call_args.kwargs['prepare_threshold'] is None
    connect.return_value.__exit__.assert_called_once_with(None, None, None)
    connect.reset_mock()
    with pytest.raises(ValueError, match='rollback'):
        with db.connection():
            raise ValueError('rollback')
    assert connect.return_value.__exit__.call_args.args[0] is ValueError


def test_pool_configuration_commits_session_settings(monkeypatch):
    connection = MagicMock()
    db._configure_connection(connection)
    connection.commit.assert_called_once_with()


def test_database_errors_do_not_expose_credentials(monkeypatch):
    monkeypatch.setenv('SUPABASE_DB_URL', 'postgresql://secret-password')
    monkeypatch.setattr(db.psycopg, 'connect', MagicMock(side_effect=psycopg.OperationalError('secret-password')))
    with pytest.raises(db.DatabaseError) as error:
        with db.connection():
            pass
    assert 'secret-password' not in str(error.value)


@pytest.mark.parametrize('password, accepted', [('abcde', False), ('abcdef', True)])
def test_account_password_minimum(monkeypatch, password, accepted):
    connection = MagicMock()
    monkeypatch.setattr(db, 'connection', connection)
    if not accepted:
        with pytest.raises(ValueError, match='at least 6 characters'):
            db.create_user('candidate', 'Candidate', password)
        connection.assert_not_called()
    else:
        monkeypatch.setattr(db, 'require', lambda c, actor, roles: {'role': 'Admin'})
        db.create_user('candidate', 'Candidate', password, actor=1, email='candidate@example.com', test_date=date.today(), iqama_no='1234567890')
        params = connection.return_value.__enter__.return_value.execute.call_args.args[1]
        assert params[0] == 'candidate'
        assert params[4] != password
        assert params[4] == db.password_hash(password, params[4].split('$')[0])
