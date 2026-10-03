from datetime import date, datetime, timezone
from io import BytesIO

from openpyxl import load_workbook

from result_export import RESULT_HEADERS, excel_bytes
from shared import format_result_datetime


def test_result_datetime_uses_saudi_arabia_time():
    assert format_result_datetime(datetime(2026, 9, 10, 8, 0, tzinfo=timezone.utc)) == '2026-09-10 11:00'
    assert format_result_datetime('2026-09-10T08:00:00Z') == '2026-09-10 11:00'
    assert format_result_datetime('2026-09-10') == '2026-09-10'


def test_results_export_contains_extended_log_columns():
    rows = [{
        'id': 7, 'candidate_name': 'Candidate', 'email': 'candidate@example.com', 'username': 'candidate',
        'designation': 'Inspector', 'iqama_no': '123', 'employee_no': 'EMP-7', 'discipline': 'Welding QC',
        'project_assignment': 'Project A', 'project_location': 'Project A', 'scheduled_test_date': date(2026, 9, 10), 'exam_date': date(2026, 9, 10),
        'created_at': '2026-09-10 08:00', 'status': 'Graded', 'mcq_score': 30, 'essay_score': 40,
        'max_possible_points': 50, 'result': 'PASS (80.0%)', 'reviewer_comments': 'Complete',
        'graded_at': '2026-09-10 09:00',
    }]
    workbook = load_workbook(BytesIO(excel_bytes(rows)))
    sheet = workbook['CTA Record Log']
    assert [cell.value for cell in sheet[1]] == RESULT_HEADERS
    assert sheet['C2'].value == 'Inspector'
    assert sheet['D2'].value == 'EMP-7'
    assert sheet['M2'].value == '2026-09-10 12:00'
    assert sheet.freeze_panes == 'A2'
    assert sheet.auto_filter.ref == sheet.dimensions
    assert len(RESULT_HEADERS) == 14
    assert len(sheet.column_dimensions) == 15
