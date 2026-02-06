"""Streamlit smoke tests.

These are not pixel/DOM tests. They execute the Streamlit scripts and assert
that the apps render without exceptions and that a few stable widgets exist.
"""

import pytest
from streamlit.testing.v1 import AppTest


pytestmark = [pytest.mark.e2e, pytest.mark.ui]


def test_streamlit_main_app__runs__no_exception():
    at = AppTest.from_file("app.py").run(timeout=30)
    assert not at.exception
    assert len(at.text_area) >= 1
    assert any(b.label == "🚀 Ask" for b in at.button)


def test_streamlit_map_viewer__runs__no_exception():
    at = AppTest.from_file("pages/1_📍_Map_Viewer.py").run(timeout=30)
    assert not at.exception
    assert any(m.label == "Displayed Plans" for m in at.metric)


def test_streamlit_plan_analyzer__runs__no_exception():
    at = AppTest.from_file("pages/2_📐_Plan_Analyzer.py").run(timeout=30)
    assert not at.exception
    assert len(at.tabs) == 5


def test_streamlit_data_management__runs__no_exception():
    at = AppTest.from_file("pages/3_💾_Data_Management.py").run(timeout=60)
    assert not at.exception
    assert any(t.label == "🗄️ Vector DB" for t in at.tabs)
