"""Report persistence and access tests using an isolated connection double."""
import json
from contextlib import contextmanager
import pytest
import database as db
import assessment_analysis


@pytest.fixture
def report_store(monkeypatch):
    row = {"id": 12, "user_id": 7, "status": "Pending Review", "analysis_reports": {}}
    answers = [{"submitted_answer": "A", "awarded_score": 1,
                "snapshot": {"q_type": "mcq", "correct_answer": "A"}}]

    class Result:
        def fetchone(self):
            return dict(row)
        def __iter__(self):
            return iter(answers)

    class Connection:
        def execute(self, query, params):
            if query.startswith("UPDATE"):
                row["analysis_reports"] = json.loads(params[0])
            return Result()

    @contextmanager
    def connection():
        yield Connection()

    monkeypatch.setattr(db, "connection", connection)
    monkeypatch.setattr(db, "require", lambda c, actor, roles: {"role": "Candidate" if actor != 1 else "Reviewer"})
    return row, answers


def test_reload_reuses_first_saved_report(report_store, monkeypatch):
    row, answers = report_store
    first = db.assessment_report(7, {"id": 12, "candidate_name": "Original"})
    answers.clear()
    monkeypatch.setattr(assessment_analysis, "analyze_assessment", lambda *args: pytest.fail("Regenerated saved report"))
    assert db.assessment_report(7, {"id": 12, "candidate_name": "Changed"}) == first
    assert db.assessment_report(1, {"id": 12}) == first


def test_grading_creates_separate_immutable_report(report_store):
    row, answers = report_store
    pending = db.assessment_report(7, {"id": 12})
    row["status"] = "Graded"
    graded = db.assessment_report(7, {"id": 12, "status": "Pending Review"})
    assert graded["is_graded"] is True
    assert pending["is_graded"] is False
    assert set(row["analysis_reports"]) == {"Pending Review", "Graded"}
    assert db.assessment_report(7, {"id": 12}) == graded


def test_candidate_cannot_read_other_candidate_report(report_store):
    with pytest.raises(ValueError, match="Assessment not found"):
        db.assessment_report(8, {"id": 12})
