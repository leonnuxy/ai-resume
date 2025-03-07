import pytest
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.resume_parser import parse_resume


def test_all_files():
    """
    Test parsing of all PDF, DOCX, and TXT files in the test_files directory.
    Ensures that the parse_resume function can handle each file without crashing.
    """
    directory = 'tests/test_files'
    for filename in os.listdir(directory):
        if filename.endswith(('.pdf', '.docx', '.txt')):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    cleaned_text, formatted_sections = parse_resume(file_path)
                assert cleaned_text is not None, f"parse_resume returned None for {filename}"
                assert formatted_sections is not None, f"parse_resume returned None for {filename}"
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='latin-1') as file:
                        cleaned_text, formatted_sections = parse_resume(file_path)
                    assert cleaned_text is not None, f"parse_resume returned None for {filename}"
                    assert formatted_sections is not None, f"parse_resume returned None for {filename}"
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='iso-8859-1') as file:
                        cleaned_text, formatted_sections = parse_resume(file_path)
                    assert cleaned_text is not None, f"parse_resume returned None for {filename}"
                    assert formatted_sections is not None, f"parse_resume returned None for {filename}"
            except Exception as e:
                pytest.fail(f"Error processing {filename}: {e}")
