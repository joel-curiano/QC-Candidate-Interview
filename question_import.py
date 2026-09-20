"""Excel question-bank import and template helpers."""
from io import BytesIO
from copy import copy
import json

from openpyxl import Workbook, load_workbook
from question_types import QUESTION_TYPES, REVIEWER_SCORED_TYPES


CORE_HEADERS = ['Discipline', 'Question type', 'Question', 'Multiple Choice options', 'Correct answer', 'Scoring rubric']

HEADERS = [
    'Discipline',
    'Question type',
    'Question',
    'Multiple Choice options',
    'Correct answer',
    'Scoring rubric',
    'Subject', 'Sub-subject', 'Scored question', 'Difficulty', 'Topic group', 'Delivery stage',
]


class QuestionImportError(ValueError):
    """User-facing validation error for question workbooks."""


def _text(value):
    return '' if value is None else str(value).strip()


def parse_questions(workbook_bytes):
    """Return validated question dictionaries from the first worksheet."""
    try:
        workbook = load_workbook(BytesIO(workbook_bytes), read_only=True, data_only=True)
    except Exception as exc:
        raise QuestionImportError('The uploaded file is not a readable Excel workbook.') from exc

    if 'Questions' not in workbook.sheetnames:
        raise QuestionImportError('The workbook must contain a Questions sheet from qc-question-template.xlsx.')
    sheet = workbook['Questions']
    rows = sheet.iter_rows(values_only=True)
    header = next(rows, None)
    normalized_header = [_text(value) for value in header[:len(HEADERS)]] if header is not None else []
    legacy_headers = CORE_HEADERS[:3] + ['MCQ options'] + CORE_HEADERS[4:]
    legacy_headers_with_points = CORE_HEADERS + ['Maximum points']
    legacy_headers_with_points_and_mcq_options = legacy_headers + ['Maximum points']
    legacy_headers_with_metadata = CORE_HEADERS + ['Subject', 'Sub-subject', 'Scored question', 'Difficulty', 'Topic group', 'Delivery stage']
    if normalized_header not in (HEADERS, legacy_headers, legacy_headers_with_points, legacy_headers_with_points_and_mcq_options, legacy_headers_with_metadata):
        raise QuestionImportError('The first row must contain the template headers in the expected order.')

    questions = []
    for row_number, row in enumerate(rows, 2):
        values = list(row[:len(HEADERS)])
        if not any(_text(value) for value in values):
            continue
        if len(values) < len(HEADERS):
            values.extend([''] * (len(HEADERS) - len(values)))
        discipline, kind, prompt, options, correct, rubric = map(_text, values[:6])
        metadata = list(row[6:12]) + ['', '', '', '', '', '']
        subject, sub_subject, scored, difficulty, topic_group, delivery_stage = map(_text, metadata[:6])
        subject = subject or 'General'; sub_subject = sub_subject or 'General'; difficulty = difficulty or 'moderate'; topic_group = topic_group or 'General'; scored = scored.lower() not in ('no', 'false', '0', 'non-scored'); delivery_stage = delivery_stage or 'standard'
        
        row_result = {'row_number': row_number, 'success': True, 'error': None, 'question': None, 'prompt': prompt}
        try:
            if not discipline or not prompt:
                raise QuestionImportError('Discipline and question are required.')
            if kind not in QUESTION_TYPES:
                raise QuestionImportError('Question type must be mcq, essay, or oral_practical.')
            if difficulty not in ('easy', 'moderate', 'difficult') or delivery_stage not in ('standard', 'oral_opening'):
                raise QuestionImportError('Difficulty and delivery stage values are invalid.')
            if delivery_stage == 'oral_opening' and (kind != 'oral_practical' or scored):
                raise QuestionImportError('Oral opening questions must be non-scored Oral-Practical questions.')
            option_separator = '\n' if '\n' in options or '\r' in options else ';'
            option_values = [value.strip() for value in options.split(option_separator) if value.strip()]
            if kind == 'mcq':
                if len(option_values) < 2 or len(set(option_values)) != len(option_values) or correct not in option_values:
                    raise QuestionImportError('Multiple Choice questions need unique options and an exact correct answer.')
            elif kind in REVIEWER_SCORED_TYPES and not rubric:
                raise QuestionImportError('Essay and Oral-Practical questions require a scoring rubric.')
            row_result['question'] = {
                'discipline': discipline,
                'kind': kind,
                'prompt': prompt,
                'options': option_values,
                'correct': correct,
                'rubric': rubric, 'subject': subject, 'sub_subject': sub_subject,
                'is_scored': scored, 'difficulty': difficulty, 'topic_group': topic_group, 'delivery_stage': delivery_stage,
            }
        except QuestionImportError as e:
            row_result['success'] = False
            row_result['error'] = str(e)
            
        questions.append(row_result)

    if not questions:
        raise QuestionImportError('The workbook does not contain any question rows.')
    return questions


def template_bytes():
    """Return a blank, formatted Excel question-bank template."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Questions'
    sheet.append(HEADERS)
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = 'A1:L1'
    widths = [22, 20, 65, 45, 35, 65, 22, 28, 18, 16, 40, 18]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[chr(64 + index)].width = width
    for cell in sheet[1]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    instructions = workbook.create_sheet('Instructions')
    instructions.append(['Question bank import instructions'])
    instructions.append(['Fill the Questions sheet and leave no completely blank rows between questions.'])
    instructions.append(['Question type must be mcq, essay, or oral_practical. For Multiple Choice questions, put one option per line in Multiple Choice options.'])
    instructions.append(['Assessment Settings determines the maximum points for each question type. Keep the headers unchanged.'])
    instructions.column_dimensions['A'].width = 110
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()

def export_questions_bytes(questions):
    """Return active question-bank rows in the re-importable template format."""
    workbook = load_workbook(BytesIO(template_bytes()))
    sheet = workbook['Questions']
    for question in questions:
        options = question.get('options') or []
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except (TypeError, ValueError):
                options = options.splitlines()
        sheet.append([
            question.get('discipline', ''),
            question.get('q_type', ''),
            question.get('question_text', ''),
            '\n'.join(str(option) for option in options),
            question.get('correct_answer', '') or '',
            question.get('rubric', '') or '', question.get('subject', 'General'), question.get('sub_subject', 'General'),
            'yes' if question.get('is_scored', True) else 'no', question.get('difficulty', 'moderate'), question.get('topic_group', 'General'), question.get('delivery_stage', 'standard'),
        ])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = 's'
    sheet.auto_filter.ref = sheet.dimensions
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()



