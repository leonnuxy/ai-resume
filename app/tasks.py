# tasks.py
from celery import Celery
from app.services.ai_analysis import analyze_resume_for_job
import os
import json
from dotenv import load_dotenv
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
import time

load_dotenv()

celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
celery.conf.update(
    task_soft_time_limit=300,  # 5 minutes soft timeout
    task_time_limit=600,      # 10 minutes hard timeout
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_acks_late=True,      # Tasks are acknowledged after execution
    task_reject_on_worker_lost=True  # Tasks are rejected if worker disconnects
)

class AnalysisError(Exception):
    """Custom exception for analysis errors"""
    pass

@celery.task(bind=True, max_retries=2)
def analyze_resume_task(self, resume_text: str, job_description: str):
    """Analyze and optimize resume against job description."""
    try:
        # Validate inputs
        if not resume_text or len(resume_text.strip()) < 100:
            raise ValueError("Resume text is too short or empty")
        
        if not job_description or len(job_description.strip()) < 50:
            raise ValueError("Job description is too short or empty")

        # Initialize progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Starting analysis...',
                'current': 0,
                'total': 100,
                'start_time': time.time()
            }
        )
        
        # Get analysis result
        result = analyze_resume_for_job(resume_text, job_description)
        
        # Validate result
        if not result or not isinstance(result, dict):
            raise AnalysisError("Invalid analysis result format")
            
        required_keys = ['missing_skills', 'improvement_suggestions', 'emphasis_suggestions', 'general_suggestions']
        if not all(key in result for key in required_keys):
            raise AnalysisError("Analysis result is missing required information")
        
        # Update progress before completion
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Finalizing analysis...',
                'current': 90,
                'total': 100
            }
        )
        
        return {
            "status": "completed",
            "result": result
        }
        
    except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
        error_data = {
            'exc_type': e.__class__.__name__,
            'exc_message': str(e),
            'error_type': 'timeout'
        }
        self.update_state(state='FAILURE', meta=error_data)
        raise
        
    except ValueError as e:
        error_data = {
            'exc_type': 'ValueError',
            'exc_message': str(e),
            'error_type': 'validation_error'
        }
        self.update_state(state='FAILURE', meta=error_data)
        raise
        
    except AnalysisError as e:
        error_data = {
            'exc_type': 'AnalysisError',
            'exc_message': str(e),
            'error_type': 'analysis_error'
        }
        self.update_state(state='FAILURE', meta=error_data)
        raise
        
    except Exception as e:
        error_data = {
            'exc_type': e.__class__.__name__,
            'exc_message': str(e),
            'error_type': 'unknown_error'
        }
        self.update_state(state='FAILURE', meta=error_data)
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        raise