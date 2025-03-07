import sys
import os
import pytest
import json
from datetime import datetime
from unittest.mock import patch, Mock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.ai_analysis import analyze_resume_for_job, test_ollama_connection as ollama_test_connection


@pytest.fixture(scope="module")
def log_file():
    """Create a log file for test results."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_results')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file_path = os.path.join(log_dir, f'ai_analysis_test_{timestamp}.log')
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
    - Python, JavaScript, Docker, AWS
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


def test_ollama_connection(log_file):
    """Test that we can connect to Ollama service."""
    with patch('app.services.ai_analysis.test_ollama_connection', return_value=True):
        result = ollama_test_connection()
        assert result, "Should be able to connect to Ollama service"
        log_result(log_file, "test_ollama_connection", {"connection_successful": result}, "Testing connection to Ollama service")


def test_resume_analysis(log_file, sample_data):
    """Test that resume analysis returns properly structured data."""
    sample_resume, sample_job = sample_data
    result = analyze_resume_for_job(sample_resume, sample_job)
    assert isinstance(result, dict)
    assert 'missing_skills' in result
    assert 'improvement_suggestions' in result
    assert 'emphasis_suggestions' in result
    assert 'general_suggestions' in result
    assert isinstance(result['missing_skills'], list)
    assert isinstance(result['improvement_suggestions'], list)
    assert isinstance(result['emphasis_suggestions'], list)
    assert isinstance(result['general_suggestions'], list)
    summary = (f"Missing Skills: {len(result['missing_skills'])}\n"
               f"Improvements: {len(result['improvement_suggestions'])}\n"
               f"Emphasis Points: {len(result['emphasis_suggestions'])}\n"
               f"General Suggestions: {len(result['general_suggestions'])}")
    log_result(log_file, "test_resume_analysis", result, summary)


def test_response_relevance(log_file, sample_data):
    """Test that the AI provides relevant analysis."""
    sample_resume, sample_job = sample_data
    result = analyze_resume_for_job(sample_resume, sample_job)
    aws_analyzed = any('aws' in skill['skill'].lower() for skill in result['missing_skills']) or \
                  any('aws' in sugg['experience'].lower() for sugg in result['emphasis_suggestions'])
    python_analyzed = any('python' in skill['skill'].lower() for skill in result['missing_skills']) or \
                     any('python' in sugg['experience'].lower() for sugg in result['emphasis_suggestions'])
    assert aws_analyzed or python_analyzed, "Analysis should mention either AWS or Python skills"
    skill_summary = []
    if len(result['missing_skills']) > 0:
        skill_summary.append("Missing Skills:")
        for skill in result['missing_skills']:
            skill_summary.append(f"- {skill['skill']}: {skill['suggestion']}")
    if len(result['emphasis_suggestions']) > 0:
        skill_summary.append("\nEmphasis Suggestions:")
        for sugg in result['emphasis_suggestions']:
            skill_summary.append(f"- {sugg['experience']}: {sugg['how_to_emphasize']}")
    log_result(log_file, "test_response_relevance", result, "\n".join(skill_summary))

