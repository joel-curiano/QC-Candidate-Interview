"""Verify persisted drafts recover answers, navigation and original timers."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace


class State(dict):
    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value


def test_restart_restores_mcq_and_essay_draft():
    source = ast.parse((Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8'))
    names = {'save_current_assessment_draft', 'save_assessment_answer', 'restore_assessment_draft'}
    nodes = [node for node in source.body if (
        isinstance(node, ast.FunctionDef) and node.name in names
        or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'ASSESSMENT_DRAFT_KEYS' for target in node.targets)
    )]
    stored = {}
    def save(candidate_id, payload):
        stored[candidate_id] = json.loads(json.dumps(payload))

    state = State(
        attempt_token='same-attempt', assessment_discipline='Welding QC',
        assessment_phase='essay', assessment_essay_index=2,
        assessment_mcq_deadline=1000, assessment_essay_started_at={11: 1100, 12: 1200},
        assessment_mcq_options={1: ['B', 'A']}, assessment_responses={1: 'B'},
        assessment_essay_pending_unanswered=[3],
        answer_12='Essay in progress without pressing Next',
    )
    streamlit = SimpleNamespace(session_state=state)
    namespace = {'st': streamlit, 'db': SimpleNamespace(save_assessment_draft=save)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'draft_helpers', 'exec'), namespace)
    namespace['save_assessment_answer'](7, 12)
    streamlit.session_state = State()
    namespace['restore_assessment_draft'](stored[7])
    restored = streamlit.session_state
    assert restored.assessment_responses == {1: 'B', 12: 'Essay in progress without pressing Next'}
    assert restored.answer_1 == 'B'
    assert restored.answer_12 == 'Essay in progress without pressing Next'
    assert restored.assessment_phase == 'essay'
    assert restored.assessment_essay_index == 2
    assert restored.assessment_mcq_deadline == 1000
    assert restored.assessment_essay_started_at == {11: 1100, 12: 1200}
    assert restored.assessment_mcq_options == {1: ['B', 'A']}
    assert restored.assessment_essay_pending_unanswered == [3]
