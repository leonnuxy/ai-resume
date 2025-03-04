# tasks.py
from celery import Celery
from app.routes.analysis import analyze_resume_for_job
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery.task(bind=True)
def analyze_resume_task(self, resume_text: str, job_description: str):
    try:
        generator = analyze_resume_for_job(resume_text, job_description)
        for chunk in generator:
            # Update task state with each valid chunk
            self.update_state(
                state='PROGRESS',
                meta={'chunk': chunk}
            )
        return {"status": "completed"}
    except Exception as e:
        return {"error": str(e)}