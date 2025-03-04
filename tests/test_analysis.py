# test_analysis.py
from app.routes.analysis import analyze_resume_for_job
import json

resume_text = """
SKILLS
• Languages: Python, Java, JavaScript
• Cloud & DevOps: AWS, Docker, Kubernetes
• Web Development: React, Node.js, REST APIs

EXPERIENCE
Software Engineer | Tech Corp
• Led development of cloud-based applications
• Implemented CI/CD pipelines
"""

job_description = """
We are looking for a Senior Software Engineer with experience in Python, AWS, and Docker.
"""

try:
    result = analyze_resume_for_job(resume_text, job_description)
    result_list = list(result)  # Convert generator to a list
    print(json.dumps(result_list, indent=4))  # Print the result in a readable format

    # Check for any "error" objects in the result_list
    for item_str in result_list:
        try:
            item = json.loads(item_str)
            if "error" in item:
                print(f"Error detected in analysis: {item['error']}")
            else:
               print(f"Successfully parsed item: {item}") #Show successfully parsed items
        except json.JSONDecodeError:
            print(f"Could not parse item: {item_str}")

except Exception as e:
    print(f"An error occurred during analysis: {e}")