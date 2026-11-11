"""Verify authorized sign-out pauses only the active assessment timer."""
import ast
from pathlib import Path
from types import SimpleNamespace


class State(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


class Clock:
    def __init__(self, value):
        self.value = value

    def time(self):
        return self.value


def timer_helpers(state, clock):
    source = ast.parse((Path(__file__).parents[1] / "app.py").read_text(encoding="utf-8"))
    names = {"resume_suspended_assessment_timer", "suspend_assessment_timer"}
    nodes = [
        node for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    namespace = {
        "st": SimpleNamespace(session_state=state),
        "time": clock,
        "MCQ_TIME_LIMIT_SECONDS": 40 * 60,
        "ESSAY_TIME_LIMIT_SECONDS": 6 * 60,
    }
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "timer_helpers", "exec"), namespace)
    return namespace


def test_mcq_timer_resumes_with_only_the_saved_time_remaining():
    state = State(assessment_phase="mcq", assessment_mcq_deadline=500)
    clock = Clock(100)
    helpers = timer_helpers(state, clock)

    assert helpers["suspend_assessment_timer"]() is True
    assert state.assessment_suspended_timer == {"phase": "mcq", "remaining_seconds": 400}

    clock.value = 1_000
    assert helpers["resume_suspended_assessment_timer"]() is True
    assert state.assessment_mcq_deadline == 1_400
    assert "assessment_suspended_timer" not in state


def test_essay_timer_resumes_with_only_the_saved_time_remaining():
    state = State(
        assessment_phase="essay",
        assessment_essay_index=0,
        assessment_essay_ids=[12],
        assessment_essay_started_at={12: 100},
    )
    clock = Clock(160)
    helpers = timer_helpers(state, clock)

    assert helpers["suspend_assessment_timer"]() is True
    assert state.assessment_suspended_timer == {
        "phase": "essay", "question_id": 12, "remaining_seconds": 300,
    }

    clock.value = 1_000
    assert helpers["resume_suspended_assessment_timer"]() is True
    assert state.assessment_essay_started_at[12] == 940


def test_schedule_exposes_the_sign_out_suspension_option():
    root = Path(__file__).parents[1]
    schedule_source = (root / "pages" / "2_Candidate_Schedules.py").read_text(encoding="utf-8")
    database_source = (root / "database.py").read_text(encoding="utf-8")

    assert "Allow the candidate to suspend the test by signing out" in schedule_source
    assert "test_suspension_allowed" in database_source
