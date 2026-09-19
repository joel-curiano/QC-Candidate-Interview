from io import BytesIO

import pytest
from openpyxl import load_workbook

from question_import import QuestionImportError, export_questions_bytes, parse_questions, template_bytes


def test_template_is_a_parseable_blank_workbook():
    workbook = load_workbook(BytesIO(template_bytes()))
    sheet = workbook['Questions']
    sheet.append(['Welding QC', 'mcq', 'Choose one', 'A\nB', 'A', ''])
    sheet.append(['Welding QC', 'essay', 'Explain the process', '', '', 'Award for evidence.'])
    sheet.append(['Welding QC', 'practical', 'Demonstrate the inspection process', '', '', 'Award for safe execution.'])
    sheet.append(['Welding QC', 'oral', 'Explain the inspection decision', '', '', 'Award for technical accuracy.'])
    sheet.append(['Welding QC', 'practical', 'Perform the inspection steps', '', '', 'Award for correct execution.'])
    output = BytesIO()
    workbook.save(output)
    assert parse_questions(output.getvalue()) == [
        {'row_number': 2, 'success': True, 'error': None, 'prompt': 'Choose one', 'question': {'discipline': 'Welding QC', 'kind': 'mcq', 'prompt': 'Choose one', 'options': ['A', 'B'], 'correct': 'A', 'rubric': ''}},
        {'row_number': 3, 'success': True, 'error': None, 'prompt': 'Explain the process', 'question': {'discipline': 'Welding QC', 'kind': 'essay', 'prompt': 'Explain the process', 'options': [], 'correct': '', 'rubric': 'Award for evidence.'}},
        {'row_number': 4, 'success': True, 'error': None, 'prompt': 'Demonstrate the inspection process', 'question': {'discipline': 'Welding QC', 'kind': 'practical', 'prompt': 'Demonstrate the inspection process', 'options': [], 'correct': '', 'rubric': 'Award for safe execution.'}},
        {'row_number': 5, 'success': True, 'error': None, 'prompt': 'Explain the inspection decision', 'question': {'discipline': 'Welding QC', 'kind': 'oral', 'prompt': 'Explain the inspection decision', 'options': [], 'correct': '', 'rubric': 'Award for technical accuracy.'}},
        {'row_number': 6, 'success': True, 'error': None, 'prompt': 'Perform the inspection steps', 'question': {'discipline': 'Welding QC', 'kind': 'practical', 'prompt': 'Perform the inspection steps', 'options': [], 'correct': '', 'rubric': 'Award for correct execution.'}},
    ]


def test_import_rejects_invalid_rows():
    workbook = load_workbook(BytesIO(template_bytes()))
    workbook['Questions'].append(['Welding QC', 'mcq', 'Choose one', 'A\nA', 'A', ''])
    output = BytesIO()
    workbook.save(output)
    results = parse_questions(output.getvalue())
    assert len(results) == 1
    assert results[0]['success'] is False
    assert 'unique options' in results[0]['error']

def test_existing_questions_export_is_reimportable():
    questions = [
        {
            'discipline': 'Welding QC',
            'q_type': 'mcq',
            'question_text': 'Choose one',
            'options': '["A", "B"]',
            'correct_answer': 'A',
            'rubric': '',
        },
        {
            'discipline': 'Civil QC',
            'q_type': 'essay',
            'question_text': 'Explain the inspection',
            'options': None,
            'correct_answer': None,
            'rubric': 'Award for evidence.',
        },
    ]

    exported = export_questions_bytes(questions)
    parsed = parse_questions(exported)

    assert [result['success'] for result in parsed] == [True, True]
    assert parsed[0]['question']['options'] == ['A', 'B']
    assert parsed[1]['question']['rubric'] == 'Award for evidence.'
