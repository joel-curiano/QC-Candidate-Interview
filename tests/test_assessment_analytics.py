from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from assessment_analytics import analytics_pdf_bytes, summarize_assessments
import shared


def _submission(project, status, mcq_score, essay_score=0, oral_score=0):
    return {
        "project_assignment": project,
        "status": status,
        "calculated_mcq_score": mcq_score,
        "calculated_mcq_max": 1,
        "calculated_essay_score": essay_score,
        "calculated_essay_max": 1,
        "calculated_oral_practical_score": oral_score,
        "calculated_oral_practical_max": 1,
    }


def _review_submission(project, status, mcq_score, essay_score=0, oral_score=0):
    return {
        "candidate_name": "Test Candidate",
        "discipline": "Test Discipline",
        "designation": "Inspector",
        "employee_no": "EMP-1",
        **_submission(project, status, mcq_score, essay_score, oral_score),
    }


def test_summarize_assessments_uses_grade_rule_and_separates_pending():
    summary = summarize_assessments(
        [
            _submission("Project A", "Graded", 1, essay_score=0.5),
            _submission("Project A", "Graded", 1, essay_score=0.495),
            _submission("Project A", "Pending Review", 1),
            _submission("Project B", "Graded", 1, essay_score=1, oral_score=1),
            _submission("", "Pending Review", 0),
        ]
    )

    assert summary["totals"] == {
        "total": 5,
        "graded": 3,
        "pending": 2,
        "passed": 2,
        "failed": 1,
        "pass_rate": pytest.approx(200 / 3),
        "fail_rate": pytest.approx(100 / 3),
        "average_score": pytest.approx(79.9666666667),
    }
    assert summary["projects"] == [
        {
            "project": "Project A",
            "total": 3,
            "graded": 2,
            "pending": 1,
            "passed": 1,
            "failed": 1,
            "pass_rate": 50,
            "fail_rate": 50,
            "average_score": pytest.approx(69.95),
        },
        {
            "project": "Project B",
            "total": 1,
            "graded": 1,
            "pending": 0,
            "passed": 1,
            "failed": 0,
            "pass_rate": 100,
            "fail_rate": 0,
            "average_score": 100,
        },
        {
            "project": "Unassigned",
            "total": 1,
            "graded": 0,
            "pending": 1,
            "passed": 0,
            "failed": 0,
            "pass_rate": None,
            "fail_rate": None,
            "average_score": None,
        },
    ]


def test_summarize_assessments_empty_result():
    summary = summarize_assessments([])

    assert summary["totals"] == {
        "total": 0,
        "graded": 0,
        "pending": 0,
        "passed": 0,
        "failed": 0,
        "pass_rate": None,
        "fail_rate": None,
        "average_score": None,
    }
    assert summary["projects"] == []


def test_analytics_pdf_includes_per_candidate_grading_summary():
    pdf = analytics_pdf_bytes(
        [
            {
                "id": 101,
                "candidate_name": "Amina Khan",
                "discipline": "Welding QC",
                "designation": "Inspector",
                "employee_no": "EMP-1",
                "exam_date": "2026-10-25",
                **_submission("Project A", "Graded", 1, essay_score=1),
            },
            {
                "id": 102,
                "candidate_name": "Bader Ali",
                "discipline": "Civil QC",
                "designation": "Engineer",
                "employee_no": "EMP-2",
                "exam_date": "2026-10-25",
                **_submission("Project A", "Pending Review", 0),
            },
        ],
        "Project A",
    )

    assert pdf.startswith(b"%PDF")
    assert b"Results by Project" not in pdf
    assert b"Grading Summary" in pdf
    assert b"Multiple Choice Grade" in pdf
    assert b"Overall Result" in pdf
    assert b"Amina Khan" in pdf
    assert b"Bader Ali" in pdf
    assert b"Helvetica-Bold" in pdf


def test_analytics_page_renders_for_reviewer(monkeypatch):
    monkeypatch.setattr(shared, "require_login", lambda: {"id": 9, "name": "Reviewer", "role": "Reviewer"})
    monkeypatch.setattr(shared, "cached_submissions", lambda actor_id: [
        _review_submission("Project A", "Graded", 1, essay_score=0.5),
        _review_submission("Project A", "Pending Review", 1),
        _review_submission("Project B", "Graded", 0),
    ])
    monkeypatch.setattr(shared, "inject_global_styles", lambda: None)
    monkeypatch.setattr(shared, "render_logo", lambda: None)
    monkeypatch.setattr(shared, "sidebar_nav", lambda user: None)

    app = AppTest.from_file(
        str(Path(__file__).parents[1] / "pages" / "4_Assessment_Analytics.py"),
        default_timeout=15,
    ).run()

    assert not app.exception
    assert {metric.label: metric.value for metric in app.metric} == {
        "Total assessments": "3",
        "Pass": "1",
        "Fail": "1",
        "Graded": "2",
        "Pending review": "1",
        "Pass rate": "50.0%",
        "Fail rate": "50.0%",
    }

    filtered_app = app.selectbox[0].set_value("Project B").run()

    assert not filtered_app.exception
    assert {metric.label: metric.value for metric in filtered_app.metric} == {
        "Total assessments": "1",
        "Pass": "0",
        "Fail": "1",
        "Graded": "1",
        "Pending review": "0",
        "Pass rate": "0.0%",
        "Fail rate": "100.0%",
    }
