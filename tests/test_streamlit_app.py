"""
Tests that Streamlit dashboard imports cleanly.
"""


def test_streamlit_app_imports():
    from src.app import streamlit_app

    assert hasattr(streamlit_app, "main")


def test_streamlit_helper_functions():
    from src.app.streamlit_app import _issues_dataframe, _resolve_incoming_files

    files = _resolve_incoming_files()
    assert isinstance(files, list)
    assert _issues_dataframe({"schema_issues": [], "drift_result": {"drift_issues": []}, "quality_issues": []}).empty
