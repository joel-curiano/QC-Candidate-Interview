"""Real PostgreSQL integration fixtures. Never point TEST_DATABASE_URL at production."""
import os
import uuid
from pathlib import Path
from contextlib import contextmanager
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
import pytest
import database as db


@pytest.fixture
def postgres_db(monkeypatch):
    url = os.environ.get('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to a disposable PostgreSQL database for integration tests.')
    schema = 'qc_test_' + uuid.uuid4().hex
    ddl = (Path(__file__).parents[1] / 'supabase/schema.sql').read_text(encoding='utf-8-sig')
    with psycopg.connect(url) as c:
        c.execute(ddl.replace('qc_portal', schema))

    @contextmanager
    def test_connection():
        with psycopg.connect(url, row_factory=dict_row, prepare_threshold=None) as c:
            c.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
            yield c

    monkeypatch.setattr(db, 'connection', test_connection)
    try:
        yield schema
    finally:
        # Only drop this fixture's fixed-prefix, random schema, never user tables.
        assert schema.startswith('qc_test_') and len(schema) == 40
        with psycopg.connect(url) as c:
            c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
