"""Exercise the real MCQ view across Streamlit widget cleanup and reruns."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def mcq_app():
    source = (Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8')
    phase = source.split('# ---- MCQ phase ----', 1)[1].split('# ---- Essay phase ----', 1)[0]
    setup = '''
import streamlit as st
import time
MCQ_TIME_LIMIT_SECONDS = 2400
user = {'id': 1}
mcq_questions = [{'id': 1, 'question_text': 'First'}, {'id': 2, 'question_text': 'Second'}]
st.session_state.setdefault('assessment_mcq_options', {1: ['A', 'B'], 2: ['A', 'B']})
responses = st.session_state.setdefault('assessment_responses', {})
def countdown_timer(*args):
    pass
def save_current_assessment_draft(*args):
    pass
def save_assessment_answer(candidate_id, question_id):
    responses[question_id] = st.session_state[f'answer_{question_id}']
def is_unanswered(question_id):
    return not st.session_state.get(f'answer_{question_id}', responses.get(question_id, ''))
'''
    test_file = Path(__file__).parents[1] / '.cache' / 'mcq_navigation_test.py'
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(setup + phase, encoding='utf-8')
    return AppTest.from_file(str(test_file)).run()


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_return_restores_answers_and_allows_completing_blanks(mcq_app):
    app = mcq_app
    app.radio[0].set_value('B').run()
    click(app, 'Continue to Essay Questions')
    assert not app.radio
    click(app, 'Return to unanswered questions')
    assert app.radio[0].value == 'B'
    assert app.radio[1].value is None
    app.radio[1].set_value('A').run()
    click(app, 'Continue to Essay Questions')
    assert app.session_state['assessment_responses'] == {1: 'B', 2: 'A'}
    assert app.session_state['assessment_phase'] == 'essay'


def test_proceed_preserves_saved_answers(mcq_app):
    app = mcq_app
    app.radio[0].set_value('B').run()
    click(app, 'Continue to Essay Questions')
    click(app, 'Proceed with unanswered questions')
    assert app.session_state['assessment_responses'] == {1: 'B', 2: '[Unanswered]'}
    assert app.session_state['assessment_mcq_unanswered_count'] == 1
