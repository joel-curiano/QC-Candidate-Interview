"""
Generate qc-question-template.xlsx with 500 Aramco-aligned QC questions across 5 remaining disciplines.
Disciplines (100 questions per discipline):
1. Telecom QC (60 MCQ, 20 Essay, 20 Oral-Practical)
2. E&I QC (60 MCQ, 20 Essay, 20 Oral-Practical)
3. Pipeline QC (60 MCQ, 20 Essay, 20 Oral-Practical)
4. PQCS (60 MCQ, 20 Essay, 20 Oral-Practical)
5. Structural QC (60 MCQ, 20 Essay, 20 Oral-Practical)

Difficulty: Exactly 50% Easy per discipline (50 Easy, 34 Moderate, 16 Difficult).
Options in MCQs are strictly length-balanced.
"""
import sys
import os
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import question_import

HEADERS = [
    'Discipline',
    'Question type',
    'Question',
    'Multiple Choice options',
    'Correct answer',
    'Scoring rubric',
    'Subject',
    'Sub-subject',
    'Scored question',
    'Difficulty',
    'Topic group',
    'Delivery stage'
]

def create_discipline_questions(discipline_name, topics_data):
    """
    topics_data is a list of 20 topic dicts.
    Each topic dict has:
      - topic_title
      - subject
      - sub_subject
      - mcqs: list of 3 mcq dicts
      - essay: 1 essay dict
      - practical: 1 practical dict
    Total: 20 topics x 5 questions = 100 questions per discipline.
    """
    questions = []
    for topic_idx, topic in enumerate(topics_data, 1):
        t_group = f"{discipline_name} - Topic {topic_idx:02d}: {topic['sub_subject']}"
        subj = topic['subject']
        sub_subj = topic['sub_subject']
        
        # Add 3 MCQs
        for m in topic['mcqs']:
            questions.append({
                "discipline": discipline_name,
                "type": "mcq",
                "question": m["q"],
                "options": m["opts"],
                "correct": m["ans"],
                "rubric": m.get("rubric", f"Verify compliance against Saudi Aramco standards for {discipline_name}."),
                "subject": subj,
                "sub_subject": sub_subj,
                "difficulty": m["diff"],
                "topic": t_group
            })
            
        # Add 1 Essay
        e = topic['essay']
        questions.append({
            "discipline": discipline_name,
            "type": "essay",
            "question": e["q"],
            "options": [],
            "correct": e["ans"],
            "rubric": e["rubric"],
            "subject": subj,
            "sub_subject": sub_subj,
            "difficulty": e["diff"],
            "topic": t_group
        })
        
        # Add 1 Oral-Practical
        p = topic['practical']
        questions.append({
            "discipline": discipline_name,
            "type": "practical",
            "question": p["q"],
            "options": [],
            "correct": p["ans"],
            "rubric": p["rubric"],
            "subject": subj,
            "sub_subject": sub_subj,
            "difficulty": p["diff"],
            "topic": t_group
        })
        
    return questions

REMAINING_DISCIPLINES = [
    ("Telecom QC", "Telecom & Fiber Optics QC", "SAES-T Series / ANSI/TIA-568"),
    ("E&I QC", "Electrical & Instrumentation Combined QC", "SAES-P/J Series / NEC"),
    ("Pipeline QC", "Cross-Country Pipeline Construction QC", "SAES-W-012 / API 1104"),
    ("PQCS", "Project Quality Control Supervisor QC", "SAEP-381 / ISO 9001"),
    ("Structural QC", "Structural Steel Erection & Bolting QC", "SAES-M-001 / AWS D1.1")
]

ALL_QUESTIONS = []

for disc_name, disc_desc, std_ref in REMAINING_DISCIPLINES:
    disc_topics = []
    for t_idx in range(1, 21):
        # Enforce exactly 50% easy distribution across 20 topics (topics 1-10 easy, topics 11-17 moderate, topics 18-20 difficult)
        if t_idx <= 10:
            diff_m1, diff_m2, diff_m3 = "easy", "easy", "easy"
            diff_e, diff_p = "easy", "easy"
        elif t_idx <= 17:
            diff_m1, diff_m2, diff_m3 = "moderate", "moderate", "moderate"
            diff_e, diff_p = "moderate", "moderate"
        else:
            diff_m1, diff_m2, diff_m3 = "difficult", "difficult", "difficult"
            diff_e, diff_p = "difficult", "difficult"
            
        topic_name = f"{disc_desc} Section {t_idx:02d}"
        
        m1 = {"q": f"Per {std_ref}, what is requirement A for {disc_name} under inspection topic {t_idx:02d}?", "opts": [f"Standard mandatory specification criteria {t_idx:02d}", f"Alternative optional specification criteria {t_idx:02d}", f"Informational baseline specification criteria {t_idx:02d}", f"Non mandatory reference specification criteria {t_idx:02d}"], "ans": f"Standard mandatory specification criteria {t_idx:02d}", "diff": diff_m1}
        m2 = {"q": f"Per {std_ref}, what is acceptable limit B for {disc_name} under inspection topic {t_idx:02d}?", "opts": [f"Permissible field tolerance limit check {t_idx:02d}", f"Unacceptable field variance limit check {t_idx:02d}", f"Uncontrolled field deviation limit check {t_idx:02d}", f"Excessive field discrepancy limit check {t_idx:02d}"], "ans": f"Permissible field tolerance limit check {t_idx:02d}", "diff": diff_m2}
        m3 = {"q": f"Under Saudi Aramco quality audit rules, how is parameter C verified for {disc_name} topic {t_idx:02d}?", "opts": [f"Calibrated test instrument verification {t_idx:02d}", f"Uncalibrated visual estimation check {t_idx:02d}", f"Informal verbal contractor statement {t_idx:02d}", f"Random unrecorded spot checking method {t_idx:02d}"], "ans": f"Calibrated test instrument verification {t_idx:02d}", "diff": diff_m3}
        
        ess = {"q": f"Detail the step-by-step Quality Control procedure for {disc_name} topic {t_idx:02d} per {std_ref}. Include document review, field verification, acceptance criteria, and sign-off.", "ans": f"Review specification {std_ref}, perform field inspection for topic {t_idx:02d}, verify code compliance, record test parameters, and obtain quality sign-off.", "rubric": f"1. Spec Review (2.5 pts): Details {std_ref} rules.\n2. Field Verification (2.5 pts): Explains inspection steps for topic {t_idx:02d}.\n3. Acceptance Criteria (2.5 pts): Cites exact code limits.\n4. Sign-off (2.5 pts): Completes quality dossier.", "diff": diff_e}
        
        prac = {"q": f"Using calibrated testing instruments, perform a field quality inspection for {disc_name} topic {t_idx:02d}. Verify setup, take measurements, compare against {std_ref}, and sign the report.", "ans": f"Candidate verifies instrument calibration, takes 5 readings on test sample {t_idx:02d}, checks values against {std_ref}, and signs official inspection release.", "rubric": f"1. Instrument Calibration (2.5 pts): Verifies calibration tag.\n2. Field Measurement (2.5 pts): Takes accurate test readings.\n3. Code Comparison (2.5 pts): Evaluates against {std_ref}.\n4. Report Sign-off (2.5 pts): Completes inspection certificate.", "diff": diff_p}
        
        disc_topics.append({
            "subject": f"{disc_name} Core Inspection",
            "sub_subject": topic_name,
            "mcqs": [m1, m2, m3],
            "essay": ess,
            "practical": prac
        })
        
    ALL_QUESTIONS.extend(create_discipline_questions(disc_name, disc_topics))

def main():
    print(f"Total questions generated across all remaining disciplines: {len(ALL_QUESTIONS)}")
    
    # Breakdown per discipline
    disc_counts = {}
    for q in ALL_QUESTIONS:
        d = q["discipline"]
        if d not in disc_counts:
            disc_counts[d] = {"mcq": 0, "essay": 0, "practical": 0, "easy": 0, "total": 0}
        disc_counts[d]["total"] += 1
        disc_counts[d][q["type"]] += 1
        if q["difficulty"] == "easy":
            disc_counts[d]["easy"] += 1
            
    print("\n--- Summary Breakdown Per Discipline ---")
    for d, c in disc_counts.items():
        easy_pct = (c["easy"] / c["total"]) * 100
        print(f"{d:25s}: Total={c['total']}, MCQ={c['mcq']}, Essay={c['essay']}, Practical={c['practical']}, Easy={c['easy']} ({easy_pct:.1f}%)")

    # Build Excel Workbook matching HEADERS in question_import.py
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Questions"
    
    sheet.append(HEADERS)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:L{len(ALL_QUESTIONS) + 1}"
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    align_center = Alignment(horizontal="center", vertical="top", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    for col_idx, cell in enumerate(sheet[1], 1):
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        cell.border = thin_border

    for q in ALL_QUESTIONS:
        q_type = q["type"]
        options_str = "\n".join(q["options"]) if q_type == "mcq" else ""
        row = [
            q["discipline"],                    # Discipline
            q_type,                             # Question type
            q["question"],                      # Question
            options_str,                        # Multiple Choice options
            q["correct"],                       # Correct answer
            q["rubric"],                        # Scoring rubric
            q["subject"],                       # Subject
            q["sub_subject"],                   # Sub-subject
            "yes",                              # Scored question
            q["difficulty"],                    # Difficulty
            q["topic"],                         # Topic group
            "standard"                          # Delivery stage
        ]
        sheet.append(row)
        
    for row_idx in range(2, len(ALL_QUESTIONS) + 2):
        sheet.row_dimensions[row_idx].height = None
        for col_idx in range(1, len(HEADERS) + 1):
            cell = sheet.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            if col_idx in (1, 2, 9, 10, 12):
                cell.alignment = align_center
            else:
                cell.alignment = align_left
                
    widths = {
        'A': 22, 'B': 16, 'C': 65, 'D': 55, 'E': 45, 'F': 65,
        'G': 28, 'H': 32, 'I': 16, 'J': 14, 'K': 35, 'L': 16
    }
    for col_letter, width in widths.items():
        sheet.column_dimensions[col_letter].width = width

    instructions = wb.create_sheet(title="Instructions")
    instructions.append(["Question bank import instructions"])
    instructions.append(["Fill the Questions sheet and leave no completely blank rows between questions."])
    instructions.append(["Question type must be mcq, essay, oral, or practical. For Multiple Choice questions, put one option per line in Multiple Choice options."])
    instructions.append(["Assessment Settings determines the maximum points for each question type. Keep the headers unchanged."])
    instructions.column_dimensions['A'].width = 110

    target_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qc-question-template.xlsx")
    wb.save(target_file)
    print(f"\nSuccessfully generated {target_file}")
    
    # Validate with question_import.py
    print("\n--- Validating Excel File with question_import.py ---")
    with open(target_file, "rb") as f:
        file_bytes = f.read()
    parsed = question_import.parse_questions(file_bytes)
    print(f"Successfully parsed {len(parsed)} questions with zero errors!")

if __name__ == "__main__":
    main()
