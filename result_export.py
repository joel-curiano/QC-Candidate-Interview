"""Excel export for the assessment results log."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


RESULT_HEADERS = [
    'Reference', 'Candidate', 'Candidate Email', 'Username', 'Designation', 'Iqama No',
    'Employee No', 'Discipline', 'Project Location', 'Scheduled Test Date', 'Exam Date',
    'Submitted (UTC)', 'Status', 'Multiple Choice Points', 'Essay Points',
    'Oral Points', 'Practicum Points', 'Practical Points', 'Maximum Points',
    'Result', 'Reviewer Comments', 'Graded (UTC)',
]


def _safe_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
        return "'" + value
    return '' if value is None else value


def _row_values(row):
    return [
        row.get('id'), row.get('candidate_name'), row.get('email', ''), row.get('username', ''),
        row.get('designation', ''), row.get('iqama_no', ''), row.get('employee_no', ''),
        row.get('discipline', ''), row.get('project_location', ''), row.get('scheduled_test_date', ''),
        row.get('exam_date', ''), row.get('created_at') or 'Legacy record', row.get('status', ''),
        row.get('mcq_score', 0), row.get('essay_only_score', 0) if row.get('status') == 'Graded' else None,
        row.get('oral_score', 0) if row.get('status') == 'Graded' else None,
        row.get('practicum_score', 0) if row.get('status') == 'Graded' else None,
        row.get('practical_score', 0) if row.get('status') == 'Graded' else None,
        row.get('max_possible_points', 0), row.get('result', ''), row.get('reviewer_comments', ''),
        row.get('graded_at', ''),
    ]


def excel_bytes(rows):
    """Return a formatted Excel workbook containing the results log."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'CTA Record Log'
    sheet.append(RESULT_HEADERS)
    for row in rows:
        sheet.append([_safe_cell(value) for value in _row_values(row)])

    header_fill = PatternFill('solid', fgColor='1F4E78')
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical='top', wrap_text=cell.column in (2, 3, 5, 8, 9, 21))

    widths = [12, 24, 30, 18, 20, 18, 18, 18, 24, 20, 16, 22, 18, 20, 16, 16, 16, 16, 18, 18, 42, 22]
    for index, width in enumerate(widths, 1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    sheet.row_dimensions[1].height = 30

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()