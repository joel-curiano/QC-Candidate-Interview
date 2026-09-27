"""Generate QC question bank template from authored discipline banks or standards.
Requirements:
- 80 MCQ, 40 Essay, 40 Oral-Practical per discipline (160 total)
- 13 disciplines (from CSV) -> 2,080 questions total
- Prioritizes authored JSON files in scripts/question_bank/{slug}.json (e.g. piping_qc.json, welding_qc.json)
- Preserves exemplars from Question-Difficulty-Guide.md
- Adheres to Question-Difficulty-Guide.md difficulty distribution (MCQ: 24/32/24, Essay: 12/16/12, Oral: 12/16/12)
"""

import argparse
import csv
import hashlib
import json
import math
import random
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT / "Question-Difficulty-Guide.md"
CSV_PATH = ROOT / "disciplines-subjects-topics.csv"
BUILD_DIR = ROOT / ".cache" / "question-bank-build"
REPORT_DIR = ROOT / "outputs" / "qc-question-bank"
OUTPUT_EXCEL = ROOT / "qc-question-template.xlsx"
QUESTION_BANK_DIR = ROOT / "scripts" / "question_bank"

TOTALS = {"mcq": 80, "essay": 40, "oral_practical": 40}
DIFFICULTIES = ("easy", "moderate", "difficult")
TYPE_LABELS = {"MCQ": "mcq", "Essay": "essay", "Oral-Practical": "oral_practical"}

DISCIPLINE_SLUGS = {
    "Cathodic Protection QC": "cathodic_protection_qc",
    "Civil QC": "civil_qc",
    "Coating QC": "coating_qc",
    "Telecom QC": "telecom_qc",
    "Electrical QC": "electrical_qc",
    "E&I QC": "e_and_i_qc",
    "Instrumentation QC": "instrumentation_qc",
    "Mechanical QC": "mechanical_qc",
    "NDT QC": "ndt_qc",
    "Piping QC": "piping_qc",
    "Welding QC": "welding_qc",
    "Pipeline QC": "pipeline_qc",
    "PQCS": "pqcs"
}

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

def load_topics():
    result = defaultdict(list)
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            result[row["Discipline"]].append({"subj": row["Subject"], "topic": row["Topic"]})
    return dict(result)

def difficulty_targets():
    guide = GUIDE_PATH.read_text(encoding="utf-8")
    result = {}
    for label, kind in TYPE_LABELS.items():
        pattern = rf"^\|\s*{re.escape(label)}\s*\|\s*(\d+)%\s*\|\s*(\d+)%\s*\|\s*(\d+)%"
        match = re.search(pattern, guide, re.M)
        if not match:
            raise ValueError(f"Missing difficulty row for {label}")
        perc = list(map(int, match.groups()))
        raw = [TOTALS[kind] * p / 100 for p in perc]
        counts = [math.floor(x) for x in raw]
        for i in sorted(range(3), key=lambda i: (raw[i] - counts[i]), reverse=True)[:TOTALS[kind] - sum(counts)]:
            counts[i] += 1
        result[kind] = dict(zip(DIFFICULTIES, counts))
    return result

def parse_exemplars():
    guide = GUIDE_PATH.read_text(encoding="utf-8")
    section = guide.split("## 4. Question Classification Exemplars by Discipline", 1)[1].split("## 5.", 1)[0]
    result = defaultdict(list)
    discipline = difficulty = kind = None
    current = None
    for line in section.splitlines():
        line = line.strip()
        if m := re.match(r"###\s+4\.\d+\s+(.+?)\s*$", line):
            discipline = m.group(1).split(" (")[0]
        elif m := re.match(r"####\s+(Easy|Moderate|Difficult)", line):
            difficulty = m.group(1).lower()
        elif line.startswith("- **Type**:"):
            kind = TYPE_LABELS.get(line.split(":", 1)[1].strip(), "mcq")
        elif line.startswith("- **Prompt**:"):
            prompt = line.split(":", 1)[1].strip()
            current = {"question": prompt, "type": kind, "difficulty": difficulty, "options": [], "answer": None, "rubric": []}
            result[discipline].append(current)
        elif current and (m := re.match(r"- ([A-D])\)\s+(.+)", line)):
            opt = m.group(2).replace("*(Correct)*", "").strip()
            if "*(Correct)*" in m.group(2):
                current["answer"] = len(current["options"])
            current["options"].append(opt)
        elif current and line.startswith("- **Rubric**:"):
            continue
        elif current and line.startswith("- ") and not line.startswith("- **"):
            current["rubric"].append(line[2:].strip())
    return dict(result)

def load_authored_bank(discipline, topics):
    slug = DISCIPLINE_SLUGS.get(discipline, discipline.lower().replace(" ", "_"))
    bank_file = QUESTION_BANK_DIR / f"{slug}.json"
    if not bank_file.exists():
        return None
    data = json.loads(bank_file.read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    if len(questions) != 160:
        return None

    subj_map = {t["topic"]: t["subj"] for t in topics}
    rows = []
    for q in questions:
        q_type = q["type"]
        topic = q.get("topic", "").strip()
        subj = subj_map.get(topic, discipline)
        opts = q.get("options", [])
        opts_str = "\n".join(opts) if q_type == "mcq" else ""
        correct_ans = opts[q["answer"]] if q_type == "mcq" and q.get("answer") is not None else ""
        rubric_str = "\n".join(q.get("rubric", [])) if isinstance(q.get("rubric"), list) else str(q.get("rubric", ""))

        rows.append({
            "discipline": discipline,
            "q_type": q_type,
            "question_text": q["question"],
            "options": opts,
            "correct_answer": correct_ans,
            "rubric": rubric_str,
            "subject": subj,
            "sub_subject": topic,
            "is_scored": True,
            "difficulty": q["difficulty"],
            "topic_group": topic,
            "delivery_stage": "standard",
            "id": q.get("id", ""),
            "source_note": q.get("source_note", "Authored question bank"),
            "exemplar": bool(q.get("exemplar"))
        })
    return rows

def generate_fallback_mcq(discipline, subj, topic, difficulty, idx):
    prompt = f"In {discipline} regarding {topic.lower()}, which of the following requirements governs inspection and acceptance per project standards?"
    opts = [
        f"Verification against approved project drawings, specifications, and applicable inspection standards for {topic.lower()}.",
        f"Reliance solely on preliminary visual observations without checking calibration certificates or approved ITP criteria.",
        f"Delegation of quality verification entirely to the subcontractor without independent quality inspection sign-off.",
        f"Postponement of inspection until final mechanical completion without intermediate stage hold or witness point checks."
    ]
    answer = idx % 4
    return {
        "question": prompt,
        "type": "mcq",
        "difficulty": difficulty,
        "options": opts,
        "answer": answer,
        "rubric": [f"Tests core knowledge of quality control requirements for {topic.lower()}."],
        "source_note": "Generated standard MCQ"
    }

def generate_fallback_essay(discipline, subj, topic, difficulty, idx):
    prompt = f"Detail the step-by-step Quality Control inspection procedure for {topic.lower()} in {discipline}. Explain the pre-inspection document review, field verification steps, acceptance criteria lookup, and quality turnover documentation."
    rubric = [
        f"Document Review: Verify approved drawings, specifications, and ITP requirements for {topic.lower()}.",
        f"Field Inspection: Execute physical inspection using calibrated tools and verify workmanship standards.",
        f"Acceptance Criteria: Check field observations against applicable project tolerances and code requirements.",
        f"Documentation & Sign-off: Complete inspection report, update tracking registers, and obtain formal sign-off."
    ]
    return {
        "question": prompt,
        "type": "essay",
        "difficulty": difficulty,
        "options": [],
        "answer": None,
        "rubric": rubric,
        "source_note": "Generated standard Essay"
    }

def generate_fallback_oral(discipline, subj, topic, difficulty, idx):
    prompt = f"You are the QC Inspector assigned to verify {topic.lower()} in {discipline}. Walk through the inspection sequence verbally: explain the required pre-requisites, how you perform the inspection, the criteria for acceptance, and what actions you take if a nonconformance is identified."
    rubric = [
        f"Pre-requisites: Verify calibration of test instruments and availability of approved inspection documents.",
        f"Inspection Execution: Describe the step-by-step technical method used to examine {topic.lower()}.",
        f"Acceptance Evaluation: State the specific pass/fail criteria and tolerance limits applied.",
        f"Reporting & Disposition: Explain the nonconformance escalation and inspection report completion process."
    ]
    return {
        "question": prompt,
        "type": "oral_practical",
        "difficulty": difficulty,
        "options": [],
        "answer": None,
        "rubric": rubric,
        "source_note": "Generated standard Oral-Practical"
    }

def build_questions():
    topics_by_disc = load_topics()
    exemplars = parse_exemplars()
    targets = difficulty_targets()
    rows = []
    uid = 1

    for discipline, topics in topics_by_disc.items():
        # Check if full authored bank exists
        authored = load_authored_bank(discipline, topics)
        if authored:
            print(f"Loaded authored question bank for {discipline} ({len(authored)} questions)")
            rows.extend(authored)
            continue

        print(f"Generating structured questions for {discipline}...")
        ex_list = exemplars.get(discipline, [])
        for ex in ex_list:
            row = {
                "discipline": discipline,
                "q_type": ex["type"],
                "question_text": ex["question"],
                "options": ex.get("options", []),
                "correct_answer": ex.get("options", [])[ex.get("answer", 0)] if ex["type"] == "mcq" else "",
                "rubric": "\n".join(ex.get("rubric", [])),
                "subject": discipline,
                "sub_subject": "",
                "is_scored": True,
                "difficulty": ex["difficulty"],
                "topic_group": "",
                "delivery_stage": "standard",
                "id": f"{discipline[:3].upper()}-{uid:05d}",
                "source_note": "Exemplar from guide",
                "exemplar": True,
            }
            uid += 1
            rows.append(row)

        needed = {k: dict(v) for k, v in targets.items()}
        for ex in ex_list:
            needed[ex["type"]][ex["difficulty"]] -= 1

        topic_cycle = [(t["subj"], t["topic"]) for t in topics]
        ti = 0

        # MCQs
        for diff in DIFFICULTIES:
            for i in range(needed["mcq"][diff]):
                subj, topic = topic_cycle[ti % len(topic_cycle)]
                ti += 1
                q = generate_fallback_mcq(discipline, subj, topic, diff, i)
                row = {
                    "discipline": discipline,
                    "q_type": "mcq",
                    "question_text": q["question"],
                    "options": q["options"],
                    "correct_answer": q["options"][q["answer"]],
                    "rubric": "\n".join(q["rubric"]),
                    "subject": subj,
                    "sub_subject": topic,
                    "is_scored": True,
                    "difficulty": diff,
                    "topic_group": topic,
                    "delivery_stage": "standard",
                    "id": f"{discipline[:3].upper()}-{uid:05d}",
                    "source_note": q["source_note"],
                    "exemplar": False,
                }
                uid += 1
                rows.append(row)

        # Essays
        for diff in DIFFICULTIES:
            for i in range(needed["essay"][diff]):
                subj, topic = topic_cycle[ti % len(topic_cycle)]
                ti += 1
                q = generate_fallback_essay(discipline, subj, topic, diff, i)
                row = {
                    "discipline": discipline,
                    "q_type": "essay",
                    "question_text": q["question"],
                    "options": [],
                    "correct_answer": "",
                    "rubric": "\n".join(q["rubric"]),
                    "subject": subj,
                    "sub_subject": topic,
                    "is_scored": True,
                    "difficulty": diff,
                    "topic_group": topic,
                    "delivery_stage": "standard",
                    "id": f"{discipline[:3].upper()}-{uid:05d}",
                    "source_note": q["source_note"],
                    "exemplar": False,
                }
                uid += 1
                rows.append(row)

        # Oral-Practical
        for diff in DIFFICULTIES:
            for i in range(needed["oral_practical"][diff]):
                subj, topic = topic_cycle[ti % len(topic_cycle)]
                ti += 1
                q = generate_fallback_oral(discipline, subj, topic, diff, i)
                row = {
                    "discipline": discipline,
                    "q_type": "oral_practical",
                    "question_text": q["question"],
                    "options": [],
                    "correct_answer": "",
                    "rubric": "\n".join(q["rubric"]),
                    "subject": subj,
                    "sub_subject": topic,
                    "is_scored": True,
                    "difficulty": diff,
                    "topic_group": topic,
                    "delivery_stage": "standard",
                    "id": f"{discipline[:3].upper()}-{uid:05d}",
                    "source_note": q["source_note"],
                    "exemplar": False,
                }
                uid += 1
                rows.append(row)

    return rows, targets

def export_to_excel(rows, targets, output_path):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Questions"

    sheet.append(HEADERS)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = f"A1:L{len(rows) + 1}"

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

    for r in rows:
        options_str = "\n".join(r["options"]) if r["q_type"] == "mcq" and isinstance(r["options"], list) else str(r.get("options", ""))
        row_vals = [
            r["discipline"],
            r["q_type"],
            r["question_text"],
            options_str,
            r["correct_answer"],
            r["rubric"],
            r["subject"],
            r["sub_subject"],
            "yes" if r.get("is_scored", True) else "no",
            r["difficulty"],
            r["topic_group"],
            r["delivery_stage"]
        ]
        sheet.append(row_vals)

    for row_idx in range(2, len(rows) + 2):
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
        'A': 24, 'B': 16, 'C': 65, 'D': 55, 'E': 45, 'F': 65,
        'G': 28, 'H': 32, 'I': 14, 'J': 14, 'K': 35, 'L': 16
    }
    for col_letter, width in widths.items():
        sheet.column_dimensions[col_letter].width = width

    instructions = wb.create_sheet(title="Instructions")
    instructions.append(["Question bank import instructions"])
    instructions.append(["Fill the Questions sheet and leave no completely blank rows between questions."])
    instructions.append(["Question type must be mcq, essay, or oral_practical. For Multiple Choice questions, put one option per line in Multiple Choice options."])
    instructions.append(["Assessment Settings determines the maximum points for each question type. Keep the headers unchanged."])
    instructions.column_dimensions['A'].width = 110

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Exported {len(rows)} rows to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate QC question bank template.")
    parser.add_argument("command", nargs="?", choices=("build",), default="build")
    args = parser.parse_args()

    rows, targets = build_questions()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    export_to_excel(rows, targets, OUTPUT_EXCEL)

    sys.path.insert(0, str(ROOT))
    import question_import
    parsed = question_import.parse_questions(OUTPUT_EXCEL.read_bytes())
    failures = [r for r in parsed if not r["success"]]
    if failures or len(parsed) != len(rows):
        print(f"Validation failures: {json.dumps(failures[:5], indent=2)}")
        raise RuntimeError(f"Validation failed: {len(failures)} errors, {len(parsed)} rows vs {len(rows)} generated")

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures else "needs_work",
        "errors": [],
        "warnings": [],
        "targets": targets,
        "total_questions": len(rows),
        "workbook_sha256": hashlib.sha256(OUTPUT_EXCEL.read_bytes()).hexdigest(),
    }
    (REPORT_DIR / "validation.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Successfully generated {len(rows)} questions and wrote {OUTPUT_EXCEL}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
