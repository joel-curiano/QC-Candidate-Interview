"""Tests for the automated candidate assessment analysis engine."""
import json
import pytest
from assessment_analysis import (
    analyze_assessment,
    analyze_essay_response,
    extract_keywords,
    parse_rubric_criteria,
    parse_snapshot,
    is_unanswered,
)


def test_parse_snapshot_and_rubric():
    # Valid dict
    d = {"id": 1, "q_type": "mcq"}
    assert parse_snapshot(d) == d

    # JSON string
    s = json.dumps(d)
    assert parse_snapshot(s) == d

    # Corrupted string
    assert parse_snapshot("invalid json") == {}

    # Rubric list
    r_list = ["Criterion A", "Criterion B"]
    assert parse_rubric_criteria(r_list) == r_list

    # Rubric JSON string
    assert parse_rubric_criteria(json.dumps(r_list)) == r_list

    # Rubric newline string
    assert parse_rubric_criteria("Point 1\nPoint 2\nPoint 3") == ["Point 1", "Point 2", "Point 3"]

    # Empty rubric
    assert parse_rubric_criteria("") == []
    assert parse_rubric_criteria(None) == []


def test_is_unanswered_check():
    assert is_unanswered("") is True
    assert is_unanswered(None) is True
    assert is_unanswered("   ") is True
    assert is_unanswered("[Unanswered]") is True
    assert is_unanswered("[Unanswered - time expired]") is True
    assert is_unanswered("[No response submitted - time expired]") is True
    assert is_unanswered("Actual answer provided") is False


def test_essay_response_evaluation():
    rubric = [
        "Verifying foundation dimensions, elevation, and anchor bolt coordinates per IFC drawings.",
        "Inspecting concrete surface chipping and ensuring sleeves are clean.",
        "Setting leveling shims and verifying equipment levelness and plumbness.",
        "Torqueing anchor bolts to specified torque value and releasing for grouting.",
    ]
    # Comprehensive answer covering all points
    good_answer = (
        "First step is verifying foundation dimensions, elevation, and anchor bolt coordinates "
        "against approved IFC drawings. Second step is inspecting concrete surface chipping down "
        "to sound aggregate and checking anchor bolt sleeves are clean. Third step is installing "
        "leveling shims and using precision level to verify horizontal levelness and vertical plumbness. "
        "Fourth step is torqueing anchor bolts per specification and releasing for epoxy grouting."
    )
    result = analyze_essay_response(
        question_text="Describe vessel leveling and foundation inspection.",
        submitted_answer=good_answer,
        rubric_criteria=rubric,
        awarded_score=8.5,
        max_points=10.0,
    )
    assert result["word_count"] > 50
    assert result["length_rating"].startswith("Comprehensive") or result["length_rating"].startswith("Moderate")
    assert result["coverage_pct"] >= 75.0
    assert len(result["covered_criteria"]) >= 3
    assert result["awarded_score"] == 8.5

    # Unanswered essay
    unanswered_result = analyze_essay_response(
        question_text="Describe vessel leveling.",
        submitted_answer="[No response submitted - time expired]",
        rubric_criteria=rubric,
        awarded_score=0.0,
        max_points=10.0,
    )
    assert unanswered_result["word_count"] == 0
    assert unanswered_result["length_rating"] == "No response submitted"
    assert unanswered_result["coverage_pct"] == 0.0
    assert len(unanswered_result["missing_criteria"]) == 4


def test_assessment_analysis_full_metrics_and_taxonomy():
    sub = {
        "id": 101,
        "candidate_name": "Test Candidate",
        "discipline": "Mechanical QC",
        "designation": "Supervisor",
        "status": "Graded",
        "exam_date": "2026-10-03",
    }

    # Build representative answer set:
    # 4 MCQs (3 correct, 1 incorrect)
    # 1 Essay (scored 8.0 / 10.0)
    # 1 Oral-Practical (scored 9.0 / 10.0)
    answers = [
        # MCQ 1 - Codes and standards (Easy) - Correct
        {
            "id": 1,
            "question_id": 1,
            "submitted_answer": "API 686",
            "awarded_score": 1.0,
            "snapshot": {
                "id": 1,
                "q_type": "mcq",
                "question_text": "Which standard governs machinery installation?",
                "correct_answer": "API 686",
                "options": ["API 686", "ASME B31.3", "AWS D1.1", "API 650"],
                "subject": "Codes and standards",
                "sub_subject": "Applicable equipment fabrication and installation standards",
                "difficulty": "easy",
                "max_points": 1,
            },
        },
        # MCQ 2 - Codes and standards (Moderate) - Correct
        {
            "id": 2,
            "question_id": 2,
            "submitted_answer": "SAEP-302",
            "awarded_score": 1.0,
            "snapshot": {
                "id": 2,
                "q_type": "mcq",
                "question_text": "Which procedure defines document hierarchy?",
                "correct_answer": "SAEP-302",
                "options": ["SAEP-302", "SAES-A-004", "SAES-L-105", "SAES-W-011"],
                "subject": "Codes and standards",
                "sub_subject": "Controlled mechanical drawings specifications and project document hierarchy",
                "difficulty": "moderate",
                "max_points": 1,
            },
        },
        # MCQ 3 - Testing and verification (Difficult) - Incorrect
        {
            "id": 3,
            "question_id": 3,
            "submitted_answer": "1.0 mm",
            "awarded_score": 0.0,
            "snapshot": {
                "id": 3,
                "q_type": "mcq",
                "question_text": "What is maximum shaft movement during nozzle bolt torque?",
                "correct_answer": "0.05 mm",
                "options": ["0.05 mm", "0.20 mm", "0.50 mm", "1.0 mm"],
                "subject": "Testing and verification",
                "sub_subject": "Alignment measurement and torque verification",
                "difficulty": "difficult",
                "max_points": 1,
            },
        },
        # MCQ 4 - Safety and field execution (Easy) - Correct
        {
            "id": 4,
            "question_id": 4,
            "submitted_answer": "Stop work immediately",
            "awarded_score": 1.0,
            "snapshot": {
                "id": 4,
                "q_type": "mcq",
                "question_text": "What action is required upon detecting an active hot work hazard?",
                "correct_answer": "Stop work immediately",
                "options": ["Stop work immediately", "Continue with caution", "Report at end of shift", "Ignore"],
                "subject": "Safety and field execution",
                "sub_subject": "Stored energy and rotating equipment controls",
                "difficulty": "easy",
                "max_points": 1,
            },
        },
        # Essay - Installation and workmanship (Moderate) - Scored 8 / 10
        {
            "id": 5,
            "question_id": 5,
            "submitted_answer": (
                "Verify foundation chipping to sound concrete aggregate, clean anchor bolt sleeves. "
                "Set baseplate shims and check elevation and levelness using precision optical instruments. "
                "Pour non-shrink epoxy grout continuously using headbox and prepare test cubes."
            ),
            "awarded_score": 8.0,
            "snapshot": {
                "id": 5,
                "q_type": "essay",
                "question_text": "Explain foundation preparation and epoxy grouting.",
                "rubric": [
                    "Verifying foundation chipping and clean anchor bolt sleeves.",
                    "Checking baseplate leveling shims and elevation.",
                    "Witnessing epoxy grout continuous placement and cube preparation.",
                    "Conducting post cure tap sounding for voids.",
                ],
                "subject": "Installation and workmanship",
                "sub_subject": "Foundation readiness grouting and anchorage",
                "difficulty": "moderate",
                "max_points": 10,
            },
        },
        # Oral-Practical - Installation and workmanship (Moderate) - Scored 9 / 10
        {
            "id": 6,
            "question_id": 6,
            "submitted_answer": "Observed candidate setting reverse dial indicators and verifying soft foot accurately.",
            "awarded_score": 9.0,
            "snapshot": {
                "id": 6,
                "q_type": "oral_practical",
                "question_text": "Demonstrate reverse dial shaft alignment and soft foot check.",
                "rubric": "Award points for soft foot verification, indicator setup, and tolerance comparison.",
                "subject": "Installation and workmanship",
                "sub_subject": "Equipment leveling alignment and coupling installation",
                "difficulty": "moderate",
                "max_points": 10,
            },
        },
    ]

    analysis = analyze_assessment(sub, answers)

    # 1. Overall metrics
    overall = analysis["overall"]
    assert overall["mcq"]["total"] == 4
    assert overall["mcq"]["correct"] == 3
    assert overall["mcq"]["incorrect"] == 1
    assert overall["mcq"]["accuracy_pct"] == 75.0

    assert overall["essay"]["total"] == 1
    assert overall["essay"]["score"] == 8.0
    assert overall["essay"]["max"] == 10.0
    assert overall["essay"]["avg_pct"] == 80.0

    assert overall["oral_practical"]["total"] == 1
    assert overall["oral_practical"]["score"] == 9.0
    assert overall["oral_practical"]["max"] == 10.0
    assert overall["oral_practical"]["avg_pct"] == 90.0

    # Weighted: MCQ 75% * 0.60 (45) + Essay 80% * 0.20 (16) + Oral 90% * 0.20 (18) = 79.0%
    assert overall["final_weighted_pct"] == 79.0
    assert overall["final_result"] == "PASS (79.0%)"

    # 2. Subject Breakdown
    subjects = analysis["subjects"]
    assert len(subjects) == 4
    subj_map = {s["subject"]: s for s in subjects}
    assert "Codes and standards" in subj_map
    assert subj_map["Codes and standards"]["percentage"] == 100.0
    assert subj_map["Codes and standards"]["status"] == "Demonstrated Strength"

    assert "Testing and verification" in subj_map
    assert subj_map["Testing and verification"]["percentage"] == 0.0
    assert subj_map["Testing and verification"]["status"] == "Critical Knowledge Gap"

    # 3. Difficulty Breakdown
    diffs = analysis["difficulties"]
    assert diffs["easy"]["count"] == 2
    assert diffs["easy"]["percentage"] == 100.0
    assert diffs["moderate"]["count"] == 3
    assert diffs["difficult"]["count"] == 1

    # 4. MCQ Diagnostics (missed questions)
    missed = analysis["mcq_diagnostics"]
    assert len(missed) == 1
    assert missed[0]["question_id"] == 3
    assert missed[0]["submitted_answer"] == "1.0 mm"
    assert missed[0]["correct_answer"] == "0.05 mm"

    # 5. Essay Evaluations
    essays = analysis["essay_evaluations"]
    assert len(essays) == 1
    assert essays[0]["coverage_pct"] >= 50.0

    # 6. Executive Summary & Reviewer Snippet
    summary = analysis["executive_summary"]
    snippet = analysis["reviewer_feedback_snippet"]
    assert "Test Candidate" in summary
    assert "Mechanical QC" in summary
    assert "PASS" in summary
    assert "Multiple Choice Performance" in snippet

    # 7. Strictly verify forbidden characters (no em dashes or double hyphens)
    all_text = (
        summary + " " + snippet + " " +
        " ".join(s["subject"] for s in subjects) + " " +
        " ".join(m["question_text"] for m in missed)
    )
    assert "--" not in all_text, "Double hyphen found in analysis output"
    assert "—" not in all_text, "Em dash found in analysis output"
    assert "–" not in all_text, "En dash found in analysis output"


def test_assessment_analysis_pending_review_status():
    sub = {
        "id": 102,
        "candidate_name": "Pending Candidate",
        "discipline": "Civil QC",
        "designation": "Inspector",
        "status": "Pending Review",
    }
    answers = [
        {
            "id": 1,
            "submitted_answer": "Option A",
            "awarded_score": 1.0,
            "snapshot": {
                "id": 1,
                "q_type": "mcq",
                "question_text": "Civil question 1",
                "correct_answer": "Option A",
                "subject": "Codes and standards",
                "sub_subject": "Applicable concrete structural and geotechnical standards",
                "difficulty": "easy",
                "max_points": 1,
            },
        },
        {
            "id": 2,
            "submitted_answer": "Option B",
            "awarded_score": 0.0,
            "snapshot": {
                "id": 2,
                "q_type": "mcq",
                "question_text": "Civil question 2",
                "correct_answer": "Option C",
                "subject": "Codes and standards",
                "sub_subject": "Controlled civil drawings specifications and project document hierarchy",
                "difficulty": "moderate",
                "max_points": 1,
            },
        },
        {
            "id": 3,
            "submitted_answer": "Candidate essay explaining concrete slump testing procedure.",
            "awarded_score": 0.0,
            "snapshot": {
                "id": 3,
                "q_type": "essay",
                "question_text": "Describe slump testing.",
                "rubric": ["Slump cone filling", "Tamping layers", "Inverted measurement", "Reporting"],
                "subject": "Testing and verification",
                "sub_subject": "Fresh concrete and compressive strength testing",
                "difficulty": "easy",
                "max_points": 10,
            },
        },
    ]

    analysis = analyze_assessment(sub, answers)
    assert analysis["status"] == "Pending Review"
    assert analysis["is_graded"] is False
    assert analysis["overall"]["final_result"] == "Pending Review"
    assert analysis["overall"]["mcq"]["accuracy_pct"] == 50.0
    assert analysis["overall"]["essay"]["completed"] == 1
    assert "Pending Review" in analysis["executive_summary"]


@pytest.mark.parametrize("answers", [[], [
    {"submitted_answer": "A", "awarded_score": 1,
     "snapshot": {"q_type": "mcq", "correct_answer": "A"}}
]])
def test_no_development_areas_does_not_crash(answers):
    report = analyze_assessment({"status": "Pending Review"}, answers)
    assert report["development_areas"] == []
    assert "Actionable Recommendations" in report["executive_summary"]


def test_pending_essay_is_not_a_knowledge_gap():
    report = analyze_assessment({"status": "Pending Review"}, [
        {"submitted_answer": "Inspection response", "awarded_score": 0,
         "snapshot": {"q_type": "essay", "subject": "Testing"}}
    ])
    assert report["development_areas"] == []
    assert report["subjects"][0]["status"] == "Pending Review"
    assert report["subjects"][0]["assessed_questions"] == 0


def test_essay_citation_and_missing_rubric_are_not_competence():
    result = analyze_essay_response("", "API 650", [
        "Explain API 650 acceptance criteria and inspection procedures"], 0, 10)
    assert result["covered_criteria"] == []
    assert "reviewer must verify" in result["feedback"]
    result = analyze_essay_response("", "Inspection response", [], 0, 10)
    assert "Rubric unavailable" in result["feedback"]


def test_unanswered_essays_are_not_counted_as_submitted():
    report = analyze_assessment({}, [{"submitted_answer": "[Unanswered]",
        "snapshot": {"q_type": "essay"}}])
    assert "answered 0 of 1" in report["executive_summary"]
    assert "0 essays submitted" in report["reviewer_feedback_snippet"]


def test_mcq_accuracy_uses_awarded_score_consistently():
    report = analyze_assessment({}, [{"submitted_answer": "A", "awarded_score": 1,
        "snapshot": {"q_type": "mcq", "correct_answer": "B"}}])
    assert report["overall"]["mcq"]["correct"] == 1
    assert report["subjects"][0]["mcq_correct"] == 1
    assert report["mcq_diagnostics"] == []
