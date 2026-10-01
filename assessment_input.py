"""Essay input that sends edits while typing and recovers interrupted edits."""
from pathlib import Path
import streamlit.components.v1 as components


essay_input = components.declare_component(
    'assessment_essay_input',
    path=str(Path(__file__).parent / 'static' / 'essay_input'),
)
