# test_analysis.py
from analysis import analyze_resume_for_job
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

result = analyze_resume_for_job(resume_text, job_description)
print(json.dumps(result, indent=4))  # Print the result in a readable format