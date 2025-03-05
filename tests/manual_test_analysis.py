import requests
import json
import time
import sys
import os

def test_ollama_connection(base_url="http://127.0.0.1:5000"):
    """Test the Ollama connection before running the analysis"""
    print("Testing Ollama connection...")
    response = requests.get(f"{base_url}/analysis/test_ollama")
    if response.status_code != 200:
        print(f"Error testing Ollama connection: {response.text}")
        return False
    return response.json().get('connected', False)

def test_resume_analysis(base_url="http://127.0.0.1:5000"):
    # First test Ollama connection
    if not test_ollama_connection(base_url):
        print("Failed to connect to Ollama. Please ensure Ollama service is running.")
        return

    # Sample resume text and job description
    resume_text = """
    Software Engineer
    
    Skills:
    - Python, JavaScript, AWS
    - Web Development, APIs
    - Database Design
    
    Experience:
    - Built scalable web applications
    - Implemented cloud solutions
    - Led development teams
    """
    
    job_description = """
    Looking for Senior Developer with AWS skills
    - Must have Python experience
    - Cloud computing background
    - API development experience
    """
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Visit the main page to initialize session
    print("Initializing session...")
    main_response = session.get(f"{base_url}/")
    if main_response.status_code != 200:
        print(f"Error accessing main page: {main_response.text}")
        return

    # Store resume text in session by simulating file upload
    print("Storing resume text...")
    upload_response = session.post(
        f"{base_url}/upload",
        files={'resume': ('resume.txt', resume_text, 'text/plain')},
        allow_redirects=True
    )
    
    if upload_response.status_code != 200:
        print(f"Error uploading resume: {upload_response.text}")
        return
    
    # Step 2: Start the analysis
    print("Starting resume analysis...")
    headers = {'Accept': 'application/json'}
    response = session.post(
        f"{base_url}/analysis/optimize",
        data={
            'job_description': job_description
        },
        headers=headers
    )
    
    if response.status_code != 202:
        print(f"Error starting analysis: {response.text}")
        return
    
    task_id = response.json()['task_id']
    print(f"Analysis started with task ID: {task_id}")
    
    # Step 3: Poll for results with timeout
    print("\nPolling for results...")
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            print("\nTimeout waiting for analysis to complete")
            return
            
        status_response = session.get(f"{base_url}/analysis/status/{task_id}")
        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.text}")
            return
            
        status_data = status_response.json()
        state = status_data.get('state')
        
        if state == 'SUCCESS':
            chunk = status_data.get('chunk')
            if chunk:
                try:
                    result = json.loads(chunk)
                    print("\nAnalysis completed successfully!")
                    print("\nResults:")
                    print(json.dumps(result, indent=2))
                except json.JSONDecodeError:
                    print(f"\nError parsing results: {chunk}")
            break
        elif state == 'FAILURE':
            print(f"\nTask failed: {status_data.get('status')}")
            break
        elif state == 'PENDING':
            print(".", end="", flush=True)
            time.sleep(1)
        else:
            print(f"\nUnexpected state: {state}")
            break

if __name__ == "__main__":
    test_resume_analysis()