import sys
import os
import pytest
import requests
import json
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


@pytest.fixture(scope="module")
def base_url():
    return "http://127.0.0.1:5000"


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

def test_e2e_workflow(base_url, sample_data):
    sample_resume, sample_job = sample_data
    # Step 1: Upload the resume
    upload_response = requests.post(
        f"{base_url}/upload",
        files={'resume': ('resume.txt', sample_resume, 'text/plain')},
        headers={'Authorization': 'Bearer YOUR_TOKEN_HERE'}  # Add authentication header
    )
    assert upload_response.status_code == 200

    # Step 2: Start the analysis
    analysis_response = requests.post(
        f"{base_url}/analysis/optimize",
        data={'job_description': sample_job},
        headers={'Accept': 'application/json'}
    )
    assert analysis_response.status_code == 202
    task_id = analysis_response.json()['task_id']

    # Step 3: Poll for results
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout + 10:
            pytest.fail("Timeout waiting for analysis to complete")
        status_response = requests.get(f"{base_url}/analysis/status/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        state = status_data.get('state')
        if state == 'SUCCESS':
            result = json.loads(status_data.get('chunk'))
            assert isinstance(result, dict)
            assert 'missing_skills' in result
            assert 'improvement_suggestions' in result
            assert 'emphasis_suggestions' in result
            assert 'general_suggestions' in result
            break
        elif state == 'FAILURE':
            pytest.fail(f"Task failed: {status_data.get('status')}")
        elif state == 'PENDING':
            time.sleep(1)
        else:
            pytest.fail(f"Unexpected state: {state}")
