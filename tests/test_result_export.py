from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from result_export import RESULT_HEADERS, excel_bytes


def test_results_export_contains_extended_log_columns():
    rows = [{
        'id': 7, 'candidate_name': 'Candidate', 'email': 'candidate@example.com', 'username': 'candidate',
        'designation': 'Inspector', 'iqama_no': '123', 'employee_no': 'EMP-7', 'discipline': 'Welding QC',
        'project_location': 'Project A', 'scheduled_test_date': date(2026, 9, 10), 'exam_date': date(2026, 9, 10),
        'created_at': '2026-09-10 08:00', 'status': 'Graded', 'mcq_score': 30, 'essay_score': 40,
        'max_possible_points': 50, 'result': 'PASS (80.0%)', 'reviewer_comments': 'Complete',
        'graded_at': '2026-09-10 09:00',
    }]
    workbook = load_workbook(BytesIO(excel_bytes(rows)))
    sheet = workbook['CTA Record Log']
    assert [cell.value for cell in sheet[1]] == RESULT_HEADERS
    assert sheet['C2'].value == 'candidate@example.com'
    assert sheet['F2'].value == '123'
    assert sheet.freeze_panes == 'A2'
    assert sheet.auto_filter.ref == sheet.dimensions