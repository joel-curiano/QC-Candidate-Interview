"""Server-side Supabase PostgreSQL storage and assessment rules."""
import hashlib
import hmac
import json
import math
import os
import secrets
import time
import psycopg
from datetime import date
from psycopg import sql
from psycopg.rows import dict_row
from contextlib import contextmanager
from pathlib import Path

DB_SCHEMA = 'qc_portal'
STARTER_DISCIPLINES = (
    'Cathodic Protection QC', 'Civil QC', 'Coating QC', 'Communications QC', 'Electrical QC', 'E&I QC', 'Instrumentation QC',
    'Mechanical QC', 'NDT QC', 'Piping QC', 'Welding QC',
    'Pipeline QC', 'PQCS',
)


class DatabaseError(ValueError):
    """Safe, user-facing database error; never includes connection credentials."""


def database_url():
    url = os.environ.get('SUPABASE_DB_URL', '').strip()
    if not url:
        import streamlit as st
        try:
            url = str(st.secrets.get('SUPABASE_DB_URL', '')).strip()
        except FileNotFoundError:
            pass
    if not url:
        raise DatabaseError('Set SUPABASE_DB_URL in Streamlit Secrets or your environment. See README.md for Supabase setup.')
    return url


@contextmanager
def connection():
    try:
        with psycopg.connect(database_url(), row_factory=dict_row, connect_timeout=10,
                             sslmode='require', prepare_threshold=None) as conn:
            conn.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(DB_SCHEMA)))
            conn.execute("SET LOCAL timezone = 'UTC'")
            conn.execute("SET LOCAL statement_timeout = '20s'")
            conn.execute("SET LOCAL lock_timeout = '10s'")
            yield conn
    except psycopg.Error:
        raise DatabaseError('Database operation failed. Check your Supabase connection, project status, and schema setup, then retry.') from None


def init_db():
    """Seed an empty question bank and add Civil QC when the discipline is missing."""
    with connection() as c:
        c.execute('SELECT pg_advisory_xact_lock(74192001)')
        c.execute('ALTER TABLE questions DROP CONSTRAINT IF EXISTS questions_q_type_check')
        c.execute("UPDATE questions SET q_type='practical' WHERE q_type='practicum'")
        c.execute("UPDATE answers SET snapshot=jsonb_set(snapshot::jsonb, '{q_type}', '\"practical\"'::jsonb) WHERE snapshot::json->>'q_type'='practicum'")
        c.execute("DELETE FROM answers WHERE submission_id IN (SELECT id FROM submissions WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days')")
        c.execute("ALTER TABLE questions ADD CONSTRAINT questions_q_type_check CHECK (q_type IN ('mcq', 'essay', 'oral', 'practical'))")
        c.execute("UPDATE questions SET max_points=1 WHERE q_type='mcq' AND max_points <> 1")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS designation TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS iqama_no TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS employee_no TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS exam_date DATE NOT NULL DEFAULT CURRENT_DATE")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS project_location TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS project_assignment TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS oral_score DOUBLE PRECISION NOT NULL DEFAULT 0")
        c.execute("ALTER TABLE submissions ADD COLUMN IF NOT EXISTS practical_score DOUBLE PRECISION NOT NULL DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS test_date DATE")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_sent_at TIMESTAMPTZ")
        c.execute("CREATE TABLE IF NOT EXISTS projects (name TEXT PRIMARY KEY)")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_projects TEXT[] NOT NULL DEFAULT '{}'")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS discipline TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS iqama_no TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS employee_no TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile_no TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS previous_schedules JSONB NOT NULL DEFAULT '[]'::jsonb")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS project_assignment TEXT NOT NULL DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS scheduled_discipline TEXT NOT NULL DEFAULT ''")
        original_questions = json.loads(Path(__file__).with_name('seed_questions.json').read_text(encoding='utf-8'))
        original_questions = [row[:4] + [row[4], row[5], 1 if row[1] == 'mcq' else row[6]] for row in original_questions]
        has_any_users = c.execute('SELECT 1 FROM users LIMIT 1').fetchone()
        
        # Only seed questions if the database is entirely empty (no questions and no users).
        if not has_any_users and not c.execute('SELECT 1 FROM questions LIMIT 1').fetchone():
            c.cursor().executemany('INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,rubric,max_points) VALUES (%s,%s,%s,%s,%s,%s,%s)', original_questions)
            essay_prompts = {
                'Electrical QC': 'Describe how you would inspect an electrical installation against approved drawings and test records. Explain how you would document and close an identified discrepancy.',
                'Instrumentation QC': 'Describe how you would review instrument calibration and loop-check records. Explain traceability checks and how you would handle a failed result.',
            }
            for discipline, essay_prompt in essay_prompts.items():
                options = ['Record and report the nonconformance', 'Ignore the result', 'Change the acceptance criteria', 'Approve without evidence']
                c.execute('INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,rubric,max_points) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                          (discipline, 'mcq', f'During a {discipline} inspection, a result does not meet the approved acceptance criteria. What should you do?', json.dumps(options), options[0], '', 10))
                c.execute('INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,rubric,max_points) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                          (discipline, 'essay', essay_prompt, None, None,
                           'Award up to 5 points each for: approved documents and criteria; inspection steps and evidence; nonconformance handling; verified closure and traceability. Adapt technical criteria to the project.', 20))

        # Include archived questions so intentional archiving is respected.
        if not has_any_users and not c.execute('SELECT 1 FROM questions WHERE discipline=%s LIMIT 1', ('Civil QC',)).fetchone():
            civil_questions = [q for q in original_questions if q[0] == 'Civil QC']
            c.cursor().executemany(
                'INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,rubric,max_points) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                civil_questions,
            )


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return f'{salt}${digest}'

def generate_password(length=12):
    """Return a password containing characters from all required categories."""
    if length < 6:
        raise ValueError('Generated passwords must be at least 6 characters.')
    groups = ('abcdefghijkmnopqrstuvwxyz', 'ABCDEFGHJKLMNPQRSTUVWXYZ', '23456789', '!@#$%&*?')
    password = [secrets.choice(group) for group in groups]
    alphabet = ''.join(groups)
    password.extend(secrets.choice(alphabet) for _ in range(length - len(password)))
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def require(c, user_id, roles):
    user = c.execute('SELECT id,username,name,email,role FROM users WHERE id=%s', (user_id,)).fetchone()
    if not user or user['role'] not in roles:
        raise ValueError('You do not have permission for this action.')
    return dict(user)

def has_users():
    with connection() as c:
        return bool(c.execute('SELECT 1 FROM users LIMIT 1').fetchone())

def create_user(username, name, password, role='Candidate', actor=None, bootstrap=False, email='', test_date=None, discipline='', iqama_no='', employee_no='', mobile_no=''):
    username, name = username.strip().lower(), name.strip()
    if not username or not name or len(password) < 6:
        raise ValueError('Enter a username, full name, and password of at least 6 characters.')
    email = email.strip().lower()
    hashed = password_hash(password)
    with connection() as c:
        c.execute('SELECT pg_advisory_xact_lock(74192002)')
        if bootstrap:
            if c.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                raise ValueError('Initial setup is already complete.')
            role = 'Admin'
        elif actor is not None:
            actor_user = require(c, actor, ('Admin', 'Reviewer'))
            if actor_user['role'] == 'Reviewer' and role != 'Candidate':
                raise ValueError('Reviewers can only create Candidate accounts.')
        else:
            raise ValueError('Only Admin and Reviewer users can create Candidate accounts.')
        if role in ('Candidate', 'Reviewer') and not email:
            raise ValueError(f'{role} email is required.')
        if role not in ('Candidate', 'Reviewer', 'Admin'):
            raise ValueError('Invalid role.')
        try:
            user_id = c.execute('INSERT INTO users(username,name,email,test_date,password,role,discipline,iqama_no,employee_no,mobile_no) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                                (username, name, email, test_date, hashed, role, discipline, iqama_no, employee_no, mobile_no)).fetchone()['id']
        except psycopg.errors.UniqueViolation as exc:
            raise ValueError('That username is already in use.') from exc
    return user_id

def authenticate(username, password):
    with connection() as c:
        user = c.execute('SELECT * FROM users WHERE username=%s', (username.strip().lower(),)).fetchone()
    stored = user['password'] if user else password_hash('dummy password', '0' * 32)
    valid_password = hmac.compare_digest(password_hash(password, stored.split('$')[0]), stored)
    if valid_password and user and (user['role'] != 'Candidate' or user['test_date'] == date.today()):
        return {k: user[k] for k in ('id', 'username', 'name', 'role', 'email', 'test_date', 'discipline', 'scheduled_discipline', 'iqama_no', 'employee_no', 'project_assignment')}
    return None

def change_password(actor, current_password, new_password):
    """Change the signed-in user's password after verifying the current password."""
    if len(new_password) < 6:
        raise ValueError('New password must be at least 6 characters.')
    with connection() as c:
        user = c.execute('SELECT id,password FROM users WHERE id=%s FOR UPDATE', (actor,)).fetchone()
        if not user:
            raise ValueError('Account not found. Please sign in again.')
        stored = user['password']
        if not hmac.compare_digest(password_hash(current_password, stored.split('$')[0]), stored):
            raise ValueError('Current password is incorrect.')
        if hmac.compare_digest(password_hash(new_password, stored.split('$')[0]), stored):
            raise ValueError('New password must be different from the current password.')
        c.execute('UPDATE users SET password=%s WHERE id=%s', (password_hash(new_password), actor))


def mark_invitation_sent(actor, candidate_id):
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        candidate = c.execute(
            "UPDATE users SET invitation_sent_at=CURRENT_TIMESTAMP "
            "WHERE id=%s AND role='Candidate' RETURNING id",
            (candidate_id,),
        ).fetchone()
        if not candidate:
            raise ValueError('Candidate account not found.')

def set_candidate_temporary_password(actor, candidate_id, temporary_password):
    if len(temporary_password) < 6:
        raise ValueError('Temporary password must be at least 6 characters.')
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        candidate = c.execute(
            "UPDATE users SET password=%s WHERE id=%s AND role='Candidate' RETURNING id",
            (password_hash(temporary_password), candidate_id),
        ).fetchone()
        if not candidate:
            raise ValueError('Candidate account not found.')


def candidate_accounts(actor):
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        return [dict(row) for row in c.execute(
            "SELECT id,username,name,email,test_date,project_assignment,scheduled_discipline,invitation_sent_at,discipline,iqama_no,employee_no,mobile_no,previous_schedules FROM users WHERE role='Candidate' ORDER BY test_date NULLS LAST, name"
        )]

def get_projects(actor):
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer', 'Candidate'))
        return [row['name'] for row in c.execute("SELECT name FROM projects ORDER BY name").fetchall()]

def add_project(actor, name):
    name = str(name).strip()
    if not name:
        raise ValueError('Project name cannot be empty.')
    with connection() as c:
        require(c, actor, ('Admin',))
        try:
            c.execute("INSERT INTO projects (name) VALUES (%s)", (name,))
        except psycopg.errors.UniqueViolation:
            raise ValueError('Project already exists.')

def delete_project(actor, name):
    with connection() as c:
        require(c, actor, ('Admin',))
        c.execute("DELETE FROM projects WHERE name=%s", (name,))

def update_staff_projects(actor, staff_id, projects):
    with connection() as c:
        require(c, actor, ('Admin',))
        staff = c.execute("SELECT role FROM users WHERE id=%s", (staff_id,)).fetchone()
        if not staff or staff['role'] not in ('Reviewer', 'Admin'):
            raise ValueError('Invalid staff account.')
        c.execute("UPDATE users SET assigned_projects=%s WHERE id=%s", (list(projects), staff_id))

def update_reviewer_email(actor, reviewer_id, email):
    email = email.strip().lower()
    if not email or '@' not in email or email.startswith('@') or email.endswith('@'):
        raise ValueError('Enter a valid Reviewer email address.')
    with connection() as c:
        require(c, actor, ('Admin',))
        reviewer = c.execute(
            "UPDATE users SET email=%s WHERE id=%s AND role='Reviewer' RETURNING id",
            (email, reviewer_id),
        ).fetchone()
        if not reviewer:
            raise ValueError('Reviewer account not found.')

def set_reviewer_temporary_password(actor, reviewer_id, temporary_password):
    if len(temporary_password) < 6:
        raise ValueError('Temporary password must be at least 6 characters.')
    with connection() as c:
        require(c, actor, ('Admin',))
        reviewer = c.execute(
            "UPDATE users SET password=%s WHERE id=%s AND role='Reviewer' RETURNING id",
            (password_hash(temporary_password), reviewer_id),
        ).fetchone()
        if not reviewer:
            raise ValueError('Reviewer account not found.')


def staff_accounts(actor):
    with connection() as c:
        require(c, actor, ('Admin',))
        return [dict(row) for row in c.execute(
            "SELECT id,username,name,email,role,assigned_projects FROM users WHERE role IN ('Reviewer', 'Admin') ORDER BY role, name"
        )]

def delete_user(actor, user_id):
    with connection() as c:
        require(c, actor, ('Admin',))
        target_user = c.execute('SELECT id, role FROM users WHERE id=%s', (user_id,)).fetchone()
        if not target_user:
            raise ValueError('Account not found.')
        if target_user['id'] == actor:
            raise ValueError('Cannot delete your own account.')
        
        if target_user['role'] == 'Candidate':
            submissions_to_delete = c.execute('SELECT id FROM submissions WHERE user_id=%s', (user_id,)).fetchall()
            if submissions_to_delete:
                sub_ids = [s['id'] for s in submissions_to_delete]
                c.execute('DELETE FROM answers WHERE submission_id = ANY(%s)', (sub_ids,))
                c.execute('DELETE FROM submissions WHERE id = ANY(%s)', (sub_ids,))
        
        elif target_user['role'] in ('Reviewer', 'Admin'):
            c.execute('UPDATE submissions SET reviewer_id=NULL WHERE reviewer_id=%s', (user_id,))
            
        c.execute('DELETE FROM users WHERE id=%s', (user_id,))

def update_candidate_schedule(actor, candidate_id, test_date, project_assignment, scheduled_discipline):
    if not test_date:
        raise ValueError('Candidate test date is required.')
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        if not project_assignment or not str(project_assignment).strip() or not scheduled_discipline or not str(scheduled_discipline).strip():
            raise ValueError('Candidate Discipline and Project Assignment are required.')
        current_user = c.execute("SELECT email, test_date, project_assignment, scheduled_discipline, discipline, previous_schedules FROM users WHERE id=%s", (candidate_id,)).fetchone()
        if not current_user:
            raise ValueError('Candidate account not found.')
        
        history = current_user.get('previous_schedules') or []
        if current_user['test_date'] and str(current_user['test_date']) != str(test_date):
            history.append({
                'test_date': str(current_user['test_date']),
                'project_assignment': current_user.get('project_assignment', ''),
                'discipline': current_user.get('scheduled_discipline') or current_user.get('discipline', ''),
                'scheduled_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            })
            
        c.execute("UPDATE users SET test_date=%s, project_assignment=%s, scheduled_discipline=%s, previous_schedules=%s::jsonb, invitation_sent_at=NULL WHERE id=%s AND role='Candidate'",
                  (test_date, str(project_assignment).strip(), str(scheduled_discipline).strip(), json.dumps(history), candidate_id))

def remove_candidate_schedule(actor, candidate_id):
    """Remove an upcoming schedule without deleting the Candidate account."""
    with connection() as c:
        require(c, actor, ('Admin',))
        candidate = c.execute(
            "UPDATE users SET test_date=NULL, project_assignment='', scheduled_discipline='', invitation_sent_at=NULL "
            "WHERE id=%s AND role='Candidate' RETURNING id",
            (candidate_id,),
        ).fetchone()
        if not candidate:
            raise ValueError('Candidate account not found.')

def questions(discipline=None, include_inactive=False):
    with connection() as c:
        rows = c.execute('''
            SELECT q.*, EXISTS(SELECT 1 FROM answers a WHERE a.question_id = q.id) as is_used
            FROM questions q
            ORDER BY q.discipline, q.id
        ''').fetchall()
    return [dict(q) for q in rows if (include_inactive or q['active']) and (discipline is None or q['discipline'] == discipline)]

def disciplines():
    with connection() as c:
        rows = c.execute('SELECT DISTINCT discipline FROM questions ORDER BY discipline').fetchall()
    return sorted(set(STARTER_DISCIPLINES) | {row['discipline'] for row in rows})

def add_question(actor, discipline, kind, prompt, options, correct, rubric, points):
    question = _validate_question(discipline, kind, prompt, options, correct, rubric, points)
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        _insert_question(c, question)

def _validate_question(discipline, kind, prompt, options, correct, rubric, points):
    options = [v.strip() for v in options if v.strip()]
    if not discipline.strip() or not prompt.strip() or not 1 <= points <= 100:
        raise ValueError('Discipline, question, and points (1-100) are required.')
    if kind not in ('mcq', 'essay', 'oral', 'practical'):
        raise ValueError('Invalid question type.')
    if kind == 'mcq' and points != 1:
        raise ValueError('Multiple Choice questions must be worth exactly 1 point.')
    if kind == 'mcq' and (len(options) < 2 or len(set(options)) != len(options) or correct not in options):
        raise ValueError('Provide unique options and an exact matching correct answer.')
    if kind in ('essay', 'oral', 'practical') and not rubric.strip():
        raise ValueError('Essay, oral, and practical questions require a scoring rubric.')
    return (discipline.strip(), kind, prompt.strip(), options, correct.strip(), rubric.strip(), points)

def _insert_question(connection, question):
    discipline, kind, prompt, options, correct, rubric, points = question
    existing = connection.execute('SELECT id FROM questions WHERE discipline=%s AND q_type=%s AND question_text=%s', (discipline, kind, prompt)).fetchone()
    if existing:
        raise ValueError('Duplicate question found.')
    connection.execute('INSERT INTO questions(discipline,q_type,question_text,options,correct_answer,rubric,max_points) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                       (discipline, kind, prompt, json.dumps(options) if kind == 'mcq' else None,
                        correct if kind == 'mcq' else None, rubric, points))

def add_questions(actor, parse_results, progress_callback=None):
    with connection() as c:
        require(c, actor, ('Admin', 'Reviewer'))
        total = len(parse_results)
        for i, result in enumerate(parse_results):
            if progress_callback:
                progress_callback(i + 1, total)
            if not result['success']:
                continue
            q = result['question']
            try:
                validated = _validate_question(q['discipline'], q['kind'], q['prompt'], q['options'], q['correct'], q['rubric'], q['points'])
                _insert_question(c, validated)
            except ValueError as e:
                result['success'] = False
                result['error'] = str(e)
    return parse_results

def autogenerate_questions(actor, discipline, kind, count, progress_callback=None):
    if not isinstance(count, int) or not (1 <= count <= 500):
        raise ValueError('Count must be between 1 and 500.')
    if kind not in ('mcq', 'essay', 'oral', 'practical'):
        raise ValueError('Invalid question type.')
    with connection() as c:
        require(c, actor, ('Admin',))
        existing_count = c.execute("SELECT COUNT(*) as cnt FROM questions WHERE discipline=%s AND q_type=%s AND question_text LIKE 'Auto-generated %'", (discipline, kind)).fetchone()['cnt']
        questions_to_insert = []
        for i in range(existing_count + 1, existing_count + count + 1):
            unique_id = secrets.token_hex(4)
            prompt = f"Auto-generated {kind.upper()} Question {i} for {discipline} ({unique_id})"
            if kind == 'mcq':
                questions_to_insert.append((discipline, kind, prompt, ['Option A', 'Option B'], 'Option A', '', 1))
            else:
                questions_to_insert.append((discipline, kind, prompt, [], '', 'Award points for any reasonable answer.', 10))
        for i, q in enumerate(questions_to_insert):
            if progress_callback:
                progress_callback(i + 1, count)
            try:
                _insert_question(c, q)
            except ValueError:
                pass

def set_active(actor, question_id, active):
    with connection() as c:
        require(c, actor, ('Admin',))
        c.execute('UPDATE questions SET active=%s WHERE id=%s', (int(active), question_id))

def delete_question(actor, question_id, force=False):
    with connection() as c:
        require(c, actor, ('Admin',))
        is_used = c.execute('SELECT 1 FROM answers WHERE question_id=%s', (question_id,)).fetchone()
        if is_used:
            if not force:
                raise ValueError('Cannot delete a question that has been answered by a candidate.')
            
            # Cascade delete the candidate submissions that used this question
            submissions_to_delete = c.execute('SELECT submission_id FROM answers WHERE question_id=%s', (question_id,)).fetchall()
            if submissions_to_delete:
                sub_ids = [s['submission_id'] for s in submissions_to_delete]
                c.execute('DELETE FROM answers WHERE submission_id = ANY(%s)', (sub_ids,))
                c.execute('DELETE FROM submissions WHERE id = ANY(%s)', (sub_ids,))

        c.execute('DELETE FROM questions WHERE id=%s', (question_id,))

def wipe_questions(actor):
    with connection() as c:
        require(c, actor, ('Admin',))
        c.execute('DELETE FROM questions WHERE id NOT IN (SELECT question_id FROM answers)')
        c.execute('UPDATE questions SET active=0')

def wipe_archived_questions(actor, progress_callback=None):
    with connection() as c:
        require(c, actor, ('Admin',))
        archived = c.execute('SELECT id FROM questions WHERE active=0').fetchall()
        total = len(archived)
        for i, q in enumerate(archived):
            if progress_callback:
                progress_callback(i + 1, total)
            delete_question(actor, q['id'], force=True)

def submit(actor, discipline, responses, token, candidate_details=None, question_ids=None):
    if not isinstance(token, str) or not token.strip():
        raise ValueError('A submission reference is required.')
    with connection() as c:
        c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (token,))
        user = require(c, actor, ('Candidate',))
        existing = c.execute('SELECT id,user_id FROM submissions WHERE token=%s', (token,)).fetchone()
        if existing:
            if existing['user_id'] != actor:
                raise ValueError('Invalid submission reference.')
            return existing['id']
        if question_ids is None:
            qs = c.execute('SELECT * FROM questions WHERE discipline=%s AND active=1 ORDER BY id FOR SHARE', (discipline,)).fetchall()
        else:
            if len(question_ids) != len(set(question_ids)):
                raise ValueError('The assessment contains duplicate questions.')
            qs = c.execute('SELECT * FROM questions WHERE discipline=%s AND active=1 AND id=ANY(%s) ORDER BY id FOR SHARE', (discipline, list(question_ids))).fetchall()
        if not qs or set(responses) != {q['id'] for q in qs}:
            raise ValueError('The question set changed. Reload the assessment before submitting.')
        if question_ids is not None:
            counts = {kind: sum(q['q_type'] == kind for q in qs) for kind in ('mcq', 'essay', 'oral', 'practical')}
            if counts != {'mcq': 20, 'essay': 5, 'oral': 5, 'practical': 5}:
                raise ValueError('The assessment must contain 20 MCQ, 5 Essay, 5 Oral, and 5 Practical Test questions.')
        for q in qs:
            answer = responses[q['id']]
            if not isinstance(answer, str) or not answer.strip() or len(answer) > 20000:
                raise ValueError('Answer every question (maximum 20,000 characters per answer).')
            if q['q_type'] == 'mcq' and answer not in json.loads(q['options']):
                raise ValueError('Choose a valid option for every MCQ.')
        details = candidate_details or {}
        candidate_name = str(details.get('name', user['name'])).strip()
        if not candidate_name:
            raise ValueError('Candidate name is required.')
        mcq_score = sum(q['max_points'] for q in qs if q['q_type'] == 'mcq' and responses[q['id']] == q['correct_answer'])
        status = 'Pending Review' if any(q['q_type'] in ('essay', 'oral', 'practical') for q in qs) else 'Graded'
        project_assignment = str(details.get('project_assignment', details.get('project_location', ''))).strip()
        sid = c.execute("INSERT INTO submissions(candidate_name,designation,iqama_no,employee_no,exam_date,project_location,project_assignment,discipline,mcq_score,max_possible_points,status,user_id,token,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP) RETURNING id",
                        (candidate_name, str(details.get('designation', '')).strip(), str(details.get('iqama_no', '')).strip(),
                         str(details.get('employee_no', '')).strip(), details.get('exam_date'), project_assignment, project_assignment,
                         discipline, mcq_score, sum(q['max_points'] for q in qs), status, actor, token)).fetchone()['id']
        for q in qs:
            score = q['max_points'] if q['q_type'] == 'mcq' and responses[q['id']] == q['correct_answer'] else 0
            c.execute('INSERT INTO answers(submission_id,question_id,submitted_answer,awarded_score,snapshot) VALUES (%s,%s,%s,%s,%s)',
                      (sid, q['id'], responses[q['id']], score, json.dumps(dict(q))))
        c.execute("UPDATE users SET test_date=NULL WHERE id=%s AND role='Candidate'", (actor,))
        return sid

def submissions(actor):
    with connection() as c:
        user = require(c, actor, ('Candidate', 'Reviewer', 'Admin'))
        assigned_projects = c.execute("SELECT assigned_projects FROM users WHERE id=%s", (actor,)).fetchone()['assigned_projects']
        return [dict(r) for r in c.execute("""
            SELECT s.*, u.email, u.username, u.test_date AS scheduled_test_date,
                   s.essay_score AS essay_only_score, s.oral_score, s.practical_score
            FROM submissions s LEFT JOIN users u ON u.id=s.user_id
            WHERE s.user_id=%s OR %s = 'Admin' OR (%s = 'Reviewer' AND s.project_location = ANY(%s))
            ORDER BY s.id DESC
        """, (actor, user['role'], user['role'], assigned_projects))]

def answer_details(actor, sid):
    with connection() as c:
        require(c, actor, ('Reviewer', 'Admin'))
        return [dict(r) for r in c.execute('SELECT * FROM answers WHERE submission_id=%s ORDER BY id', (sid,))]

def grade(actor, sid, scores, comments):
    with connection() as c:
        require(c, actor, ('Reviewer', 'Admin'))
        sub = c.execute('SELECT * FROM submissions WHERE id=%s FOR UPDATE', (sid,)).fetchone()
        if not sub or sub['status'] == 'Graded':
            raise ValueError('This assessment has already been graded or is unavailable.')
        essays = [dict(a) for a in c.execute('SELECT * FROM answers WHERE submission_id=%s', (sid,)) if json.loads(a['snapshot'])['q_type'] in ('essay', 'oral', 'practical')]
        if set(scores) != {a['id'] for a in essays}:
            raise ValueError('Score every essay before finalizing.')
        for a in essays:
            score = scores[a['id']]
            if not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= json.loads(a['snapshot'])['max_points']:
                raise ValueError("Each score must be within the question's point range.")
            c.execute('UPDATE answers SET awarded_score=%s WHERE id=%s', (score, a['id']))
        typed_scores = {kind: sum(scores[a['id']] for a in essays if json.loads(a['snapshot'])['q_type'] == kind) for kind in ('essay', 'oral', 'practical')}
        c.execute("UPDATE submissions SET essay_score=%s,oral_score=%s,practical_score=%s,status='Graded',reviewer_comments=%s,reviewer_id=%s,graded_at=CURRENT_TIMESTAMP WHERE id=%s",
                  (typed_scores['essay'], typed_scores['oral'], typed_scores['practical'], comments.strip(), actor, sid))

def result(sub):
    if sub['status'] != 'Graded':
        return 'Pending Review'
    percentage = 100 * (sub['mcq_score'] + sub['essay_score']) / sub['max_possible_points'] if sub['max_possible_points'] else 0
    return f"{'PASS' if percentage >= 70 else 'FAIL'} ({percentage:.1f}%)"
