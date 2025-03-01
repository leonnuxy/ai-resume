# tasks.py
from celery import Celery
from analysis import analyze_resume_for_job  # Import your analysis function
import time
from dotenv import load_dotenv
load_dotenv()

# Configure Celery
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
#The broker URL specifies how Celery connects to the message broker (Redis).
#The backend URL specifies where Celery will store the results of tasks

@celery.task(bind=True)
def analyze_resume_task(self, resume_text, job_description):
    time.sleep(5)
    """
    Asynchronous task to analyze a resume.
    """
    try:
        analysis = analyze_resume_for_job(resume_text, job_description)
        # For now, just return the analysis.  Later, we'll store it.
        return analysis
    except Exception as e:
        # Handle exceptions.  You might want to log them or retry the task.
        raise self.retry(exc=e, countdown=5, max_retries=3) #retry the task up to 3 times with a 5-second delay between retries