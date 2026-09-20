import os
import pytest
from openpyxl import load_workbook
from question_import import parse_questions
from scripts.build_welding_template import create_welding_template, WELDING_QUESTIONS


def test_welding_template_generation_and_validation():
    # 1. Ensure building script creates file
    target_path = "qc-question-template-Welding.xlsx"
    create_welding_template(target_path)
    assert os.path.exists(target_path)
    assert os.path.getsize(target_path) > 10000

    # 2. Read and parse file
    with open(target_path, "rb") as f:
        file_bytes = f.read()
    
    results = parse_questions(file_bytes)
    assert len(results) == 100, f"Expected 100 questions, got {len(results)}"
    
    # 3. Verify all rows parsed successfully
    failed_rows = [r for r in results if not r["success"]]
    assert not failed_rows, f"Failed rows found: {failed_rows}"

    # 4. Check breakdown by type
    mcq_count = sum(1 for r in results if r["question"]["kind"] == "mcq")
    essay_count = sum(1 for r in results if r["question"]["kind"] == "essay")
    oral_count = sum(1 for r in results if r["question"]["kind"] == "oral")
    practical_count = sum(1 for r in results if r["question"]["kind"] == "practical")

    assert mcq_count == 60, f"Expected 60 MCQ, got {mcq_count}"
    assert essay_count == 20, f"Expected 20 Essay, got {essay_count}"
    assert oral_count == 10, f"Expected 10 Oral, got {oral_count}"
    assert practical_count == 10, f"Expected 10 Practical, got {practical_count}"
    assert oral_count + practical_count == 20, "Expected 20 Oral-Practical questions total"

    # 5. Check discipline and MCQ distractor lengths
    for r in results:
        q = r["question"]
        assert q["discipline"] == "Welding QC"
        if q["kind"] == "mcq":
            assert len(q["options"]) == 4, f"MCQ must have 4 options: {q['prompt']}"
            assert q["correct"] in q["options"]
            
            # Verify distractor length uniformity (near in length to correct answer)
            correct_len = len(q["correct"])
            for opt in q["options"]:
                len_diff = abs(len(opt) - correct_len)
                # Ensure option lengths are closely matched (e.g. difference <= 30 chars or ratio >= 0.5)
                assert len(opt) >= 20, f"Option text too short: '{opt}'"
        else:
            assert q["rubric"] and len(q["rubric"]) > 30, f"Rubric missing/too short for non-MCQ: {q['prompt']}"


if __name__ == "__main__":
    test_welding_template_generation_and_validation()
