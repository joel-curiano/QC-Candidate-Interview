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
