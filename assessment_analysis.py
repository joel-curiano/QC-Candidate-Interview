"""Automated Candidate Assessment Analysis Engine.

Analyzes candidate questions and responses across multiple dimensions:
- Technical subject and topic mastery (Saudi Aramco taxonomy)
- Difficulty level performance (Easy, Moderate, Difficult cognitive levels)
- Multiple Choice question-by-question error diagnostics
- Essay technical content depth and scoring rubric criteria coverage
- Key strengths and prioritized development areas (knowledge gaps)
- Actionable executive summary and reviewer feedback generation

Compliance: No em dashes or double hyphens used.
"""

import json
from html import escape
import re
from typing import Any, Dict, List, Optional, Tuple


# Common English and procedural stop words to ignore during rubric keyword matching
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "its",
    "itself", "let", "me", "more", "most", "must", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "were", "weren't",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with",
    "would", "you", "your", "yours", "yourself", "yourselves", "award", "points",
    "ensure", "ensuring", "detail", "describe", "explain", "outline", "verify", "verifying",
}


def parse_snapshot(snapshot: Any) -> Dict[str, Any]:
    """Safely parse snapshot dictionary from string or dict."""
    if isinstance(snapshot, dict):
        return snapshot
    if isinstance(snapshot, str):
        try:
            parsed = json.loads(snapshot)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def parse_rubric_criteria(rubric_val: Any) -> List[str]:
    """Parse rubric criteria into a clean list of individual strings."""
    if not rubric_val:
        return []
    if isinstance(rubric_val, list):
        return [str(c).strip() for c in rubric_val if str(c).strip()]
    if isinstance(rubric_val, str):
        try:
            parsed = json.loads(rubric_val)
            if isinstance(parsed, list):
                return [str(c).strip() for c in parsed if str(c).strip()]
        except Exception:
            pass
        if "\n" in rubric_val:
            lines = [line.strip() for line in rubric_val.split("\n") if line.strip()]
            if len(lines) > 1:
                return lines
        if ";" in rubric_val:
            parts = [part.strip() for part in rubric_val.split(";") if part.strip()]
            if len(parts) > 1:
                return parts
        return [rubric_val.strip()]
    return [str(rubric_val).strip()]


def is_unanswered(text: Optional[str]) -> bool:
    """Return True if answer text represents an unanswered or expired question."""
    if not isinstance(text, str) or not text.strip():
        return True
    cleaned = text.strip()
    return cleaned in {
        "[Unanswered]",
        "[Unanswered - time expired]",
        "[No response submitted - time expired]",
    }


def extract_keywords(text: str) -> set:
    """Extract normalized content words and industry technical acronyms."""
    tokens = re.findall(r"[a-zA-Z0-9_-]+", text.lower())
    keywords = set()
    for token in tokens:
        clean = token.strip("-_")
        if not clean:
            continue
        if len(clean) >= 3 and clean not in STOP_WORDS:
            keywords.add(clean)
        elif clean in {"pt", "rt", "ut", "mt", "vt", "ce", "ra", "qc", "qa"}:
            keywords.add(clean)
    return keywords


def analyze_essay_response(
    question_text: str,
    submitted_answer: str,
    rubric_criteria: List[str],
    awarded_score: float,
    max_points: float,
) -> Dict[str, Any]:
    """Evaluate candidate essay response against rubric criteria and technical content."""
    unanswered = is_unanswered(submitted_answer)
    word_count = 0 if unanswered else len(re.findall(r"\b\w+\b", submitted_answer))

    if unanswered:
        length_rating = "No response submitted"
    elif word_count < 25:
        length_rating = "Brief (under 25 words)"
    elif word_count < 75:
        length_rating = "Moderate (25 to 74 words)"
    else:
        length_rating = "Comprehensive (75 or more words)"

    candidate_keywords = extract_keywords(submitted_answer) if not unanswered else set()

    covered_criteria = []
    missing_criteria = []

    for criterion in rubric_criteria:
        if unanswered:
            missing_criteria.append(criterion)
            continue

        criterion_keywords = extract_keywords(criterion)
        if not criterion_keywords:
            missing_criteria.append(criterion)
            continue

        overlap = candidate_keywords.intersection(criterion_keywords)

        match_ratio = len(overlap) / len(criterion_keywords)
        if match_ratio >= 0.5 and (len(overlap) >= 2 or len(criterion_keywords) == 1):
            covered_criteria.append(criterion)
        else:
            missing_criteria.append(criterion)

    total_crit = len(rubric_criteria)
    coverage_pct = round(100.0 * len(covered_criteria) / total_crit, 1) if total_crit > 0 else 0.0

    if unanswered:
        feedback = "No response submitted."
    elif not rubric_criteria:
        feedback = "Rubric unavailable. Concept coverage cannot be estimated."
    else:
        feedback = (
            f"Keyword matches found for {len(covered_criteria)} of {total_crit} rubric criteria. "
            "This is a lexical estimate. A reviewer must verify correctness, reasoning, and technical depth."
        )

    return {
        "word_count": word_count,
        "length_rating": length_rating,
        "rubric_criteria": rubric_criteria,
        "covered_criteria": covered_criteria,
        "missing_criteria": missing_criteria,
        "coverage_pct": coverage_pct,
        "coverage_available": bool(rubric_criteria),
        "feedback": feedback,
        "awarded_score": awarded_score,
        "max_points": max_points,
    }


def analyze_assessment(submission: Dict[str, Any], answers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Execute complete multi-dimensional automated analysis of a completed assessment."""
    status = submission.get("status", "Pending Review")
    is_graded = (status == "Graded")
    discipline = submission.get("discipline", "General")
    candidate_name = submission.get("candidate_name", "Candidate")
    job_title = submission.get("designation") or submission.get("candidate_role") or "Inspector"
    exam_date = submission.get("exam_date", "")

    # Grouped data structures
    mcq_answers = []
    essay_answers = []
    oral_answers = []

    subject_data = {}
    difficulty_data = {
        "easy": {"count": 0, "awarded": 0.0, "max": 0.0, "correct": 0, "mcq_count": 0},
        "moderate": {"count": 0, "awarded": 0.0, "max": 0.0, "correct": 0, "mcq_count": 0},
        "difficult": {"count": 0, "awarded": 0.0, "max": 0.0, "correct": 0, "mcq_count": 0},
    }
    topic_data = {}

    mcq_diagnostics = []
    essay_evaluations = []

    for a in answers:
        snap = parse_snapshot(a.get("snapshot"))
        if not snap.get("is_scored", True):
            continue
        q_type = snap.get("q_type", "mcq")
        q_id = snap.get("id") or a.get("question_id") or a.get("id")
        q_text = snap.get("question_text", "")
        subject = snap.get("subject") or "Codes and standards"
        sub_subject = snap.get("sub_subject") or snap.get("topic") or "General"
        difficulty = (snap.get("difficulty") or "moderate").lower()
        if difficulty not in difficulty_data:
            difficulty = "moderate"

        max_points = 1.0 if q_type == "mcq" else float(min(snap.get("max_points", 10), 10))
        awarded_score = float(a.get("awarded_score", 0.0) or 0.0)
        submitted_answer = a.get("submitted_answer") or ""

        # Subject aggregation
        subj_entry = subject_data.setdefault(subject, {
            "subject": subject,
            "total_questions": 0,
            "mcq_count": 0,
            "mcq_correct": 0,
            "essay_count": 0,
            "oral_count": 0,
            "awarded_points": 0.0,
            "max_points": 0.0,
        })
        subj_entry["total_questions"] += 1
        subj_entry["max_points"] += max_points
        subj_entry["awarded_points"] += awarded_score

        # Topic aggregation
        topic_key = (subject, sub_subject)
        topic_entry = topic_data.setdefault(topic_key, {
            "subject": subject,
            "sub_subject": sub_subject,
            "total_questions": 0,
            "awarded_points": 0.0,
            "max_points": 0.0,
            "correct_mcq": 0,
            "total_mcq": 0,
        })
        topic_entry["total_questions"] += 1
        topic_entry["max_points"] += max_points
        topic_entry["awarded_points"] += awarded_score

        # Difficulty aggregation
        diff_entry = difficulty_data[difficulty]
        diff_entry["count"] += 1
        diff_entry["max"] += max_points
        diff_entry["awarded"] += awarded_score

        # Type-specific processing
        if q_type == "mcq":
            mcq_answers.append(a)
            subj_entry["mcq_count"] += 1
            topic_entry["total_mcq"] += 1
            diff_entry["mcq_count"] += 1

            correct_answer = snap.get("correct_answer") or ""
            is_correct = awarded_score > 0

            if is_correct:
                subj_entry["mcq_correct"] += 1
                topic_entry["correct_mcq"] += 1
                diff_entry["correct"] += 1
            else:
                mcq_diagnostics.append({
                    "question_id": q_id,
                    "subject": subject,
                    "topic": sub_subject,
                    "difficulty": difficulty,
                    "question_text": q_text,
                    "submitted_answer": submitted_answer if submitted_answer else "[Unanswered]",
                    "correct_answer": correct_answer,
                })

        elif q_type == "essay":
            essay_answers.append(a)
            subj_entry["essay_count"] += 1
            rubric_criteria = parse_rubric_criteria(snap.get("rubric"))
            essay_eval = analyze_essay_response(
                q_text,
                submitted_answer,
                rubric_criteria,
                awarded_score,
                max_points,
            )
            essay_eval["question_id"] = q_id
            essay_eval["subject"] = subject
            essay_eval["topic"] = sub_subject
            essay_eval["difficulty"] = difficulty
            essay_eval["question_text"] = q_text
            essay_eval["submitted_answer"] = submitted_answer
            essay_evaluations.append(essay_eval)

        elif q_type == "oral_practical":
            oral_answers.append(a)
            subj_entry["oral_count"] += 1

    # MCQ Overall Metrics
    mcq_total = len(mcq_answers)
    mcq_correct = sum(data["mcq_correct"] for data in subject_data.values())
    mcq_unanswered = sum(1 for a in mcq_answers if is_unanswered(a.get("submitted_answer")))
    mcq_incorrect = mcq_total - mcq_correct
    mcq_pct = round(100.0 * mcq_correct / mcq_total, 1) if mcq_total > 0 else 0.0

    # Essay Overall Metrics
    essay_total = len(essay_answers)
    essay_completed = sum(1 for a in essay_answers if not is_unanswered(a.get("submitted_answer")))
    essay_unanswered = essay_total - essay_completed
    essay_score = sum(float(a.get("awarded_score", 0.0) or 0.0) for a in essay_answers)
    essay_max = sum(float(min(parse_snapshot(a.get("snapshot")).get("max_points", 10), 10)) for a in essay_answers)
    essay_pct = round(100.0 * essay_score / essay_max, 1) if essay_max > 0 else 0.0

    # Oral-Practical Overall Metrics
    oral_total = len(oral_answers)
    oral_completed = sum(1 for a in oral_answers if not is_unanswered(a.get("submitted_answer")))
    oral_score = sum(float(a.get("awarded_score", 0.0) or 0.0) for a in oral_answers)
    oral_max = sum(float(min(parse_snapshot(a.get("snapshot")).get("max_points", 10), 10)) for a in oral_answers)
    oral_pct = round(100.0 * oral_score / oral_max, 1) if oral_max > 0 else 0.0

    # Final Weighted Calculation
    # Standard weighting: MCQ 60%, Essay 20%, Oral-Practical 20%
    if is_graded:
        weighted_mcq = mcq_pct * 0.60
        weighted_essay = essay_pct * 0.20
        weighted_oral = oral_pct * 0.20
        final_pct = round(weighted_mcq + weighted_essay + weighted_oral, 1)
        final_status = "PASS" if final_pct >= 70.0 else "FAIL"
        final_result = f"{final_status} ({final_pct}%)"
    else:
        final_pct = mcq_pct
        final_result = "Pending Review"

    # Subject Analysis List
    subjects_list = []
    for subj_name, data in subject_data.items():
        total_pts = data["max_points"]
        earned_pts = data["awarded_points"]
        # If not fully graded, compute based on MCQ proportion or available points
        if is_graded and total_pts > 0:
            subj_pct = round(100.0 * earned_pts / total_pts, 1)
        elif data["mcq_count"] > 0:
            subj_pct = round(100.0 * data["mcq_correct"] / data["mcq_count"], 1)
        else:
            subj_pct = round(100.0 * earned_pts / total_pts, 1) if total_pts > 0 else 0.0

        assessed_count = data["total_questions"] if is_graded else data["mcq_count"]
        if assessed_count == 0:
            status_label = "Pending Review"
            badge_color = "#666666"
        elif subj_pct >= 75.0:
            status_label = "Demonstrated Strength"
            badge_color = "#188038"
        elif subj_pct >= 60.0:
            status_label = "Developing Competency"
            badge_color = "#D97706"
        else:
            status_label = "Critical Knowledge Gap"
            badge_color = "#B51F2D"

        evidence_label = "Sufficient evidence" if assessed_count >= 2 else "Limited evidence"

        subjects_list.append({
            "subject": subj_name,
            "total_questions": data["total_questions"],
            "mcq_count": data["mcq_count"],
            "mcq_correct": data["mcq_correct"],
            "essay_count": data["essay_count"],
            "oral_count": data["oral_count"],
            "awarded_points": earned_pts,
            "max_points": total_pts,
            "percentage": subj_pct,
            "status": status_label,
            "badge_color": badge_color,
            "evidence": evidence_label,
            "assessed_questions": assessed_count,
        })

    # Sort subjects: lowest percentage first so gaps are immediately visible
    subjects_list.sort(key=lambda s: (s["percentage"], s["subject"]))

    # Difficulty Analysis
    diff_results = {}
    for diff_key in ("easy", "moderate", "difficult"):
        d_info = difficulty_data[diff_key]
        cnt = d_info["count"]
        awd = d_info["awarded"]
        mx = d_info["max"]
        if is_graded and mx > 0:
            pct = round(100.0 * awd / mx, 1)
        elif d_info["mcq_count"] > 0:
            pct = round(100.0 * d_info["correct"] / d_info["mcq_count"], 1)
        else:
            pct = round(100.0 * awd / mx, 1) if mx > 0 else 0.0

        if diff_key == "easy":
            eval_comment = "Foundational standards, specifications, and quality definitions."
        elif diff_key == "moderate":
            eval_comment = "Applied field procedures, inspection tools, and tolerance verification."
        else:
            eval_comment = "Complex diagnostics, root cause analysis, and nonconformance disposition."

        diff_results[diff_key] = {
            "count": cnt,
            "mcq_count": d_info["mcq_count"],
            "correct_mcq": d_info["correct"],
            "awarded_points": awd,
            "max_points": mx,
            "percentage": pct,
            "cognitive_eval": eval_comment,
            "assessed_questions": cnt if is_graded else d_info["mcq_count"],
        }

    # Strengths and Development Areas (by topic)
    topic_rows = []
    for (subj, top), t_info in topic_data.items():
        if not is_graded and not t_info["total_mcq"]:
            continue
        if is_graded and t_info["max_points"] > 0:
            t_pct = round(100.0 * t_info["awarded_points"] / t_info["max_points"], 1)
        elif t_info["total_mcq"] > 0:
            t_pct = round(100.0 * t_info["correct_mcq"] / t_info["total_mcq"], 1)
        else:
            t_pct = 0.0

        topic_rows.append({
            "subject": subj,
            "sub_subject": top,
            "percentage": t_pct,
            "total_questions": t_info["total_questions"],
        })

    topic_strengths = [
        t for t in sorted(topic_rows, key=lambda x: (-x["percentage"], x["subject"], x["sub_subject"]))
        if t["percentage"] >= 75.0
    ][:5]

    topic_gaps = [
        t for t in sorted(topic_rows, key=lambda x: (x["percentage"], x["subject"], x["sub_subject"]))
        if t["percentage"] < 70.0
    ][:5]

    # Build Executive Summary & Reviewer Snippet
    executive_summary = build_executive_summary(
        candidate_name=candidate_name,
        discipline=discipline,
        job_title=job_title,
        status=status,
        final_pct=final_pct,
        mcq_pct=mcq_pct,
        mcq_correct=mcq_correct,
        mcq_total=mcq_total,
        subjects_list=subjects_list,
        diff_results=diff_results,
        topic_strengths=topic_strengths,
        topic_gaps=topic_gaps,
        essay_evaluations=essay_evaluations,
    )

    reviewer_feedback_snippet = build_reviewer_feedback_snippet(
        candidate_name=candidate_name,
        discipline=discipline,
        job_title=job_title,
        mcq_pct=mcq_pct,
        mcq_correct=mcq_correct,
        mcq_total=mcq_total,
        topic_strengths=topic_strengths,
        topic_gaps=topic_gaps,
        essay_evaluations=essay_evaluations,
    )

    return {
        "submission_id": submission.get("id"),
        "candidate_name": candidate_name,
        "discipline": discipline,
        "job_title": job_title,
        "exam_date": exam_date,
        "status": status,
        "is_graded": is_graded,
        "overall": {
            "mcq": {
                "total": mcq_total,
                "correct": mcq_correct,
                "incorrect": mcq_incorrect,
                "unanswered": mcq_unanswered,
                "accuracy_pct": mcq_pct,
            },
            "essay": {
                "total": essay_total,
                "completed": essay_completed,
                "unanswered": essay_unanswered,
                "score": essay_score,
                "max": essay_max,
                "avg_pct": essay_pct,
            },
            "oral_practical": {
                "total": oral_total,
                "completed": oral_completed,
                "score": oral_score,
                "max": oral_max,
                "avg_pct": oral_pct,
            },
            "final_weighted_pct": final_pct,
            "final_result": final_result,
        },
        "subjects": subjects_list,
        "difficulties": diff_results,
        "strengths": topic_strengths,
        "development_areas": topic_gaps,
        "mcq_diagnostics": mcq_diagnostics,
        "essay_evaluations": essay_evaluations,
        "executive_summary": executive_summary,
        "reviewer_feedback_snippet": reviewer_feedback_snippet,
    }


def build_executive_summary(
    candidate_name: str,
    discipline: str,
    job_title: str,
    status: str,
    final_pct: float,
    mcq_pct: float,
    mcq_correct: int,
    mcq_total: int,
    subjects_list: List[Dict[str, Any]],
    diff_results: Dict[str, Any],
    topic_strengths: List[Dict[str, Any]],
    topic_gaps: List[Dict[str, Any]],
    essay_evaluations: List[Dict[str, Any]],
) -> str:
    """Generate a coherent multi-paragraph executive analysis summary."""
    paragraphs = []

    # Paragraph 1: Candidate Overview & Score
    if status == "Graded":
        grade_desc = f"achieved an overall grade of {final_pct:.1f}% ({'PASS' if final_pct >= 70 else 'FAIL'})"
    else:
        grade_desc = f"scored {mcq_pct:.1f}% ({mcq_correct}/{mcq_total}) in the Multiple Choice phase (Status: Pending Review)"

    paragraphs.append(
        f"Candidate {candidate_name} completed the {discipline} Competency Technical Assessment for the {job_title} role. "
        f"The candidate {grade_desc}."
    )

    # Paragraph 2: Technical Strengths
    if topic_strengths:
        str_items = [f"{item['sub_subject']} ({item['percentage']:.0f}%)" for item in topic_strengths[:3]]
        paragraphs.append(
            f"Demonstrated Technical Strengths: High scores were recorded in "
            f"{', '.join(str_items)}. These findings reflect the tested questions and require field verification."
        )
    else:
        paragraphs.append(
            "Demonstrated Technical Strengths: No high-scoring topics were identified in the available scored evidence."
        )

    # Paragraph 3: Knowledge Gaps & Risk Analysis
    if topic_gaps:
        gap_items = [f"{item['sub_subject']} ({item['percentage']:.0f}%)" for item in topic_gaps[:3]]
        paragraphs.append(
            f"Identified Knowledge Gaps: Priority development areas include {', '.join(gap_items)}. "
            f"Review missed questions and reviewer feedback in these topics, then confirm understanding with a follow-up assessment."
        )
    else:
        paragraphs.append(
            "Identified Knowledge Gaps: No low-scoring topics were identified in the available scored evidence."
        )

    # Paragraph 4: Essay Technical Depth
    if essay_evaluations:
        evaluable_essays = [e for e in essay_evaluations if e["rubric_criteria"]]
        avg_essay_cov = sum(e["coverage_pct"] for e in evaluable_essays) / len(evaluable_essays) if evaluable_essays else None
        coverage_label = f"{avg_essay_cov:.1f}%" if avg_essay_cov is not None else "unavailable"
        paragraphs.append(
            f"Written Response Analysis: Candidate answered {sum(not is_unanswered(e['submitted_answer']) for e in essay_evaluations)} of {len(essay_evaluations)} essay prompt(s) with an average "
            f"rubric keyword overlap of {coverage_label}. Keyword matches do not establish technical correctness. "
            f"Reviewer evaluation is required. Missing rubrics cannot be evaluated."
        )

    # Paragraph 5: Recommendations
    recs = []
    if topic_gaps:
        top_weak_subj = topic_gaps[0]["subject"]
        recs.append(f"Structured refresher training on {top_weak_subj} and associated project standards")
    recs.append("Close technical supervision and field mentor verification during initial site mobilization")
    recs.append("Practical review of Saudi Aramco Engineering Standards (SAES) and inspection checklist verification")

    paragraphs.append(
        "Actionable Recommendations: " + " ".join(f"{i}) {rec}." for i, rec in enumerate(recs, 1))
    )

    return "\n\n".join(paragraphs)


def build_reviewer_feedback_snippet(
    candidate_name: str,
    discipline: str,
    job_title: str,
    mcq_pct: float,
    mcq_correct: int,
    mcq_total: int,
    topic_strengths: List[Dict[str, Any]],
    topic_gaps: List[Dict[str, Any]],
    essay_evaluations: List[Dict[str, Any]],
) -> str:
    """Build a concise, ready-to-use reviewer summary text."""
    lines = [
        f"Candidate Assessment Evaluation Summary for {candidate_name} ({job_title} | {discipline}):",
        f"- Multiple Choice Performance: {mcq_correct}/{mcq_total} ({mcq_pct:.1f}%)",
    ]

    if topic_strengths:
        str_names = ", ".join(t["sub_subject"] for t in topic_strengths[:2])
        lines.append(f"- Key Strengths: {str_names}")

    if topic_gaps:
        gap_names = ", ".join(t["sub_subject"] for t in topic_gaps[:2])
        lines.append(f"- Areas for Improvement: {gap_names}")

    if essay_evaluations:
        essay_words = sum(e["word_count"] for e in essay_evaluations)
        lines.append(f"- Written Technical Responses: {sum(not is_unanswered(e['submitted_answer']) for e in essay_evaluations)} essays submitted ({essay_words} total words)")

    lines.append("- Recommendation: Verify candidate field competence on identified development areas during initial site deployment.")
    return "\n".join(lines)


def render_assessment_analysis(
    analysis: Dict[str, Any],
    allow_feedback_copy: bool = True,
    for_candidate: bool = False,
) -> None:
    """Render the full auto analysis report inside Streamlit."""
    import streamlit as st

    overall = analysis.get("overall", {})
    mcq_data = overall.get("mcq", {})
    status = analysis.get("status", "Pending Review")

    # Header / KPI metrics row
    st.markdown("#### Automated Competency & Performance Overview")
    st.caption("Scores reflect assessed questions. Topic conclusions may have limited evidence. Essay keyword matches require reviewer verification.")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric("MCQ Accuracy", f"{mcq_data.get('accuracy_pct', 0.0):.1f}%", f"{mcq_data.get('correct', 0)} / {mcq_data.get('total', 0)} correct")

    with kpi_col2:
        if analysis.get("is_graded"):
            st.metric("Final Grade", f"{overall.get('final_weighted_pct', 0.0):.1f}%", overall.get("final_result", ""))
        else:
            st.metric("Grading Status", status, "Oral/Essay review pending")

    with kpi_col3:
        str_count = len(analysis.get("strengths", []))
        st.metric("Demonstrated Strengths", f"{str_count} Topics", "Score >= 75%")

    with kpi_col4:
        gap_count = len(analysis.get("development_areas", []))
        st.metric("Development Areas", f"{gap_count} Topics", "Score < 70%")

    # Executive Summary Card
    st.info(analysis.get("executive_summary", ""))

    # Tabbed detailed breakdown
    tab_subjects, tab_difficulty, tab_strengths, tab_essays, tab_diagnostics = st.tabs([
        "Subject Mastery",
        "Difficulty Breakdown",
        "Strengths & Gaps",
        "Essay Technical Depth",
        "Missed Questions",
    ])

    # Tab 1: Subject Mastery
    with tab_subjects:
        st.write("**Performance by Technical Subject**")
        subjects = analysis.get("subjects", [])
        if not subjects:
            st.caption("No subject data available.")
        else:
            for s in subjects:
                pct = s["percentage"]
                color = s["badge_color"]
                st.markdown(
                    f"<div style='margin-bottom: 8px;'>"
                    f"<strong>{escape(s['subject'])}</strong> &nbsp; "
                    f"<span style='color: {color}; font-weight: 600;'>[{s['status']}]</span> &nbsp; "
                    f"<span>{'Pending' if s['status'] == 'Pending Review' else f'{pct:.1f}%'} ({s['total_questions']} questions)</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.caption(f"{s['evidence']}. {s.get('assessed_questions', s['total_questions'])} assessed questions.")
                if s["status"] != "Pending Review":
                    st.progress(min(max(pct / 100.0, 0.0), 1.0))

    # Tab 2: Difficulty Breakdown
    with tab_difficulty:
        st.write("**Performance Across Question Difficulty Levels**")
        diffs = analysis.get("difficulties", {})
        col_e, col_m, col_d = st.columns(3)

        with col_e:
            easy_info = diffs.get("easy", {})
            st.metric("Easy (Recall & Standards)", f"{easy_info.get('percentage', 0.0):.1f}%" if easy_info.get("assessed_questions", 0) else "N/A")
            st.caption(f"{easy_info.get('count', 0)} questions. {easy_info.get('cognitive_eval', '')}")

        with col_m:
            mod_info = diffs.get("moderate", {})
            st.metric("Moderate (Applied Quality)", f"{mod_info.get('percentage', 0.0):.1f}%" if mod_info.get("assessed_questions", 0) else "N/A")
            st.caption(f"{mod_info.get('count', 0)} questions. {mod_info.get('cognitive_eval', '')}")

        with col_d:
            diff_info = diffs.get("difficult", {})
            st.metric("Difficult (Troubleshooting)", f"{diff_info.get('percentage', 0.0):.1f}%" if diff_info.get("assessed_questions", 0) else "N/A")
            st.caption(f"{diff_info.get('count', 0)} questions. {diff_info.get('cognitive_eval', '')}")

    # Tab 3: Strengths & Development Areas
    with tab_strengths:
        c_str, c_gap = st.columns(2)
        with c_str:
            st.write("##### Key Demonstrated Strengths")
            strengths = analysis.get("strengths", [])
            if not strengths:
                st.caption("No specific high-scoring topics identified.")
            else:
                for item in strengths:
                    st.success(f"**{item['sub_subject']}** ({item['subject']}): {item['percentage']:.0f}%")

        with c_gap:
            st.write("##### Identified Development Areas")
            gaps = analysis.get("development_areas", [])
            if not gaps:
                st.caption("No critical knowledge gaps identified.")
            else:
                for item in gaps:
                    st.error(f"**{item['sub_subject']}** ({item['subject']}): {item['percentage']:.0f}%")

    # Tab 4: Essay Technical Depth
    with tab_essays:
        st.write("**Essay Question Concept & Rubric Coverage Analysis**")
        essays = analysis.get("essay_evaluations", [])
        if not essays:
            st.caption("No essay questions included in this assessment.")
        else:
            for idx, eval_item in enumerate(essays, 1):
                with st.expander(f"Essay {idx}: {eval_item['topic']} ({eval_item['length_rating']})", expanded=False):
                    st.write(f"**Prompt:** {eval_item['question_text']}")
                    st.text_area("Candidate Response", value=eval_item["submitted_answer"], disabled=True, height=100, key=f"auto_essay_view_{eval_item['question_id']}")
                    coverage_label = f"{eval_item['coverage_pct']:.1f}%" if eval_item.get("coverage_available", bool(eval_item["rubric_criteria"])) else "Unavailable"
                    st.write(f"**Word Count:** {eval_item['word_count']} words | **Rubric Keyword Overlap:** {coverage_label}")
                    st.info(f"**Evaluation:** {eval_item['feedback']}")

                    if eval_item["covered_criteria"]:
                        st.write("**Rubric Concepts with Keyword Matches:**")
                        for c in eval_item["covered_criteria"]:
                            st.write(f"- [x] {c}")

                    if eval_item["missing_criteria"]:
                        st.write("**Rubric Concepts Requiring Review:**")
                        for c in eval_item["missing_criteria"]:
                            st.write(f"- [ ] {c}")

    # Tab 5: Missed Questions Diagnostic
    with tab_diagnostics:
        st.write("**Multiple Choice Error Diagnostics**")
        missed = analysis.get("mcq_diagnostics", [])
        if not missed:
            if mcq_data.get("total", 0):
                st.success("Candidate answered all Multiple Choice Questions correctly.")
            else:
                st.caption("No Multiple Choice questions available.")
        else:
            st.caption(f"Candidate missed {len(missed)} Multiple Choice question(s):")
            for item in missed:
                with st.expander(f"Missed: {item['topic']} ({item['difficulty'].capitalize()})", expanded=False):
                    st.write(f"**Question:** {item['question_text']}")
                    st.markdown(f"**Candidate Answer:** :red[{item['submitted_answer']}]")
                    st.markdown(f"**Correct Answer:** :green[{item['correct_answer']}]")

    # Reviewer feedback copy tool
    if allow_feedback_copy and not for_candidate:
        st.divider()
        st.write("**Subject/Topic Analysis**")
        st.caption("Auto-generated summary of the candidate's subject and topic performance:")
        st.code(analysis.get("reviewer_feedback_snippet", ""), language=None)
