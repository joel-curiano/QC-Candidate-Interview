"""Excel question-bank import and template helpers."""
from io import BytesIO
from copy import copy

from openpyxl import Workbook, load_workbook


HEADERS = [
    'Discipline',
    'Question type',
    'Question',
    'Multiple Choice options',
    'Correct answer',
    'Scoring rubric',
    'Maximum points',
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

    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    header = next(rows, None)
    normalized_header = [_text(value) for value in header[:len(HEADERS)]] if header is not None else []
    legacy_headers = HEADERS[:3] + ['MCQ options'] + HEADERS[4:]
    if normalized_header not in (HEADERS, legacy_headers):
        raise QuestionImportError('The first row must contain the template headers in the expected order.')

    questions = []
    for row_number, row in enumerate(rows, 2):
        values = list(row[:len(HEADERS)])
        if not any(_text(value) for value in values):
            continue
        if len(values) < len(HEADERS):
            values.extend([''] * (len(HEADERS) - len(values)))
        discipline, kind, prompt, options, correct, rubric, points = map(_text, values)
        
        row_result = {'row_number': row_number, 'success': True, 'error': None, 'question': None, 'prompt': prompt}
        try:
            if not discipline or not prompt:
                raise QuestionImportError('Discipline and question are required.')
            if kind not in ('mcq', 'essay', 'practicum', 'oral', 'practical'):
                raise QuestionImportError('Question type must be mcq, essay, practicum, oral, or practical.')
            try:
                max_points = int(float(points))
            except ValueError as exc:
                raise QuestionImportError('Maximum points must be a whole number from 1 to 100.') from exc
            if not 1 <= max_points <= 100:
                raise QuestionImportError('Maximum points must be a whole number from 1 to 100.')
            option_values = [value.strip() for value in options.replace(';', '\n').splitlines() if value.strip()]
            if kind == 'mcq':
                if len(option_values) < 2 or len(set(option_values)) != len(option_values) or correct not in option_values:
                    raise QuestionImportError('Multiple Choice questions need unique options and an exact correct answer.')
                if max_points != 1:
                    raise QuestionImportError('Multiple Choice questions must have Maximum points set to 1.')
            elif not rubric:
                raise QuestionImportError('Essay, oral, and practical questions require a scoring rubric.')
            row_result['question'] = {
                'discipline': discipline,
                'kind': kind,
                'prompt': prompt,
                'options': option_values,
                'correct': correct,
                'rubric': rubric,
                'points': max_points,
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
    sheet.auto_filter.ref = 'A1:G1'
    widths = [22, 16, 65, 45, 35, 65, 16]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[chr(64 + index)].width = width
    for cell in sheet[1]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    instructions = workbook.create_sheet('Instructions')
    instructions.append(['Question bank import instructions'])
    instructions.append(['Fill the Questions sheet and leave no completely blank rows between questions.'])
    instructions.append(['Question type must be mcq, essay, practicum, oral, or practical. For Multiple Choice questions, put one option per line in Multiple Choice options.'])
    instructions.append(['MCQ rows must use Maximum points = 1. Essay, oral, practicum, and practical rows may use a whole number from 1 to 100. Keep the headers unchanged.'])
    instructions.column_dimensions['A'].width = 110
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
