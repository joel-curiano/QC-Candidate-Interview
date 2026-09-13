from io import BytesIO

import pytest
from openpyxl import load_workbook

from question_import import QuestionImportError, parse_questions, template_bytes


def test_template_is_a_parseable_blank_workbook():
    workbook = load_workbook(BytesIO(template_bytes()))
    sheet = workbook['Questions']
    sheet.append(['Welding QC', 'mcq', 'Choose one', 'A\nB', 'A', '', 1])
    sheet.append(['Welding QC', 'essay', 'Explain the process', '', '', 'Award for evidence.', 20])
    sheet.append(['Welding QC', 'practicum', 'Demonstrate the inspection process', '', '', 'Award for safe execution.', 30])
    sheet.append(['Welding QC', 'oral', 'Explain the inspection decision', '', '', 'Award for technical accuracy.', 15])
    sheet.append(['Welding QC', 'practical', 'Perform the inspection steps', '', '', 'Award for correct execution.', 25])
    output = BytesIO()
    workbook.save(output)
    assert parse_questions(output.getvalue()) == [
        {'row_number': 2, 'success': True, 'error': None, 'prompt': 'Choose one', 'question': {'discipline': 'Welding QC', 'kind': 'mcq', 'prompt': 'Choose one', 'options': ['A', 'B'], 'correct': 'A', 'rubric': '', 'points': 1}},
        {'row_number': 3, 'success': True, 'error': None, 'prompt': 'Explain the process', 'question': {'discipline': 'Welding QC', 'kind': 'essay', 'prompt': 'Explain the process', 'options': [], 'correct': '', 'rubric': 'Award for evidence.', 'points': 20}},
        {'row_number': 4, 'success': True, 'error': None, 'prompt': 'Demonstrate the inspection process', 'question': {'discipline': 'Welding QC', 'kind': 'practicum', 'prompt': 'Demonstrate the inspection process', 'options': [], 'correct': '', 'rubric': 'Award for safe execution.', 'points': 30}},
        {'row_number': 5, 'success': True, 'error': None, 'prompt': 'Explain the inspection decision', 'question': {'discipline': 'Welding QC', 'kind': 'oral', 'prompt': 'Explain the inspection decision', 'options': [], 'correct': '', 'rubric': 'Award for technical accuracy.', 'points': 15}},
        {'row_number': 6, 'success': True, 'error': None, 'prompt': 'Perform the inspection steps', 'question': {'discipline': 'Welding QC', 'kind': 'practical', 'prompt': 'Perform the inspection steps', 'options': [], 'correct': '', 'rubric': 'Award for correct execution.', 'points': 25}},
    ]


def test_import_rejects_invalid_rows():
    workbook = load_workbook(BytesIO(template_bytes()))
    workbook['Questions'].append(['Welding QC', 'mcq', 'Choose one', 'A\nA', 'A', '', 10])
    output = BytesIO()
    workbook.save(output)
    results = parse_questions(output.getvalue())
    assert len(results) == 1
    assert results[0]['success'] is False
    assert 'unique options' in results[0]['error']
