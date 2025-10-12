import os
import pytest

def test_import_app():
    __import__("app")

def test_basic_prompt_files_exist():
    # Ensure core prompt templates exist (adjust as needed)
    base = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
    assert os.path.isdir(base), "prompts/ directory missing"