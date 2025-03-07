import pytest
import os
import sys
import tempfile
import json
from unittest.mock import patch, Mock
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.resume_parser import parse_resume
from app.services.ai_analysis import analyze_resume_for_job


@pytest.fixture(scope="module")
def log_file():
    """Create a log file for test results."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_results')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file_path = os.path.join(log_dir, f'integration_test_{timestamp}.log')
    return log_file_path


@pytest.fixture
def sample_data():
    """Sample resume and job description for testing."""
    sample_resume = """
    John Doe
    Software Engineer

    Experience:
    - Senior Developer at Tech Corp (2018-Present)
      * Led team of 5 developers
      * Implemented cloud solutions

    Skills:
    - Python, JavaScript, Docker
    - Agile methodologies
    """
    sample_job = """
    Senior Software Engineer

    Requirements:
    - 5+ years of experience in Python
    - Experience with AWS and cloud technologies
    - Strong leadership skills
    - Knowledge of React and modern JavaScript
    """
    return sample_resume, sample_job


def log_result(log_file, test_name: str, result: dict, additional_info: str = None):
    """Log test results to file."""
    with open(log_file, 'a') as f:
        f.write(f"\n{'=' * 50}\n")
        f.write(f"Test: {test_name}\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 50}\n\n")
        if additional_info:
            f.write(f"Additional Info:\n{additional_info}\n\n")
        f.write("Analysis Result:\n")
        f.write(json.dumps(result, indent=2))
        f.write("\n\n")


def test_integration(sample_data, log_file):
    """
    Test the integration of resume parsing and AI analysis.
    """
    sample_resume, sample_job = sample_data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp_resume:
        temp_resume.write(sample_resume.encode('utf-8'))
        temp_resume_path = temp_resume.name

    try:
        # Parse the resume
        cleaned_text, formatting = parse_resume(temp_resume_path)

        # Analyze the resume for the job
        analysis_result = analyze_resume_for_job(cleaned_text, sample_job)

        # Check that the analysis result is a dictionary
        assert isinstance(analysis_result, dict)

        # Check that the analysis result contains expected keys
        assert 'missing_skills' in analysis_result
        assert 'improvement_suggestions' in analysis_result
        assert 'emphasis_suggestions' in analysis_result
        assert 'general_suggestions' in analysis_result
        log_result(log_file, "test_integration", analysis_result, "resume_parsing and AI analysis")

    finally:
        # Clean up the temporary file
        os.remove(temp_resume_path)
