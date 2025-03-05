# tasks.py
from celery import Celery
from app.services.ai_analysis import analyze_resume_for_job
import os
import json
from dotenv import load_dotenv
from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
import time
from config.celery import CustomRedisBackend

load_dotenv()

# Initialize Celery with the custom backend
celery = Celery(__name__, 
               broker='redis://localhost:6379/0', 
               backend='redis://localhost:6379/0',
               backend_cls=CustomRedisBackend)

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
        # Validate and normalize inputs
        if not resume_text or not isinstance(resume_text, str):
            error_info = {
                'exc_type': 'ValueError',
                'exc_message': "Resume text must be a string",
                'exc_module': 'builtins',
                'exc_cls': 'ValueError'
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise ValueError(error_info['exc_message'])
            
        if len(resume_text.strip()) < 100:
            error_info = {
                'exc_type': 'ValueError',
                'exc_message': "Resume text is too short",
                'exc_module': 'builtins',
                'exc_cls': 'ValueError'
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise ValueError(error_info['exc_message'])
        
        if not job_description or len(job_description.strip()) < 50:
            error_info = {
                'exc_type': 'ValueError',
                'exc_message': "Job description is too short or empty",
                'exc_module': 'builtins',
                'exc_cls': 'ValueError'
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise ValueError(error_info['exc_message'])

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
        
        # Validate result structure before proceeding
        if not result or not isinstance(result, dict):
            error_info = {
                'exc_type': 'AnalysisError',
                'exc_message': "Invalid analysis result format",
                'exc_module': 'app.tasks',
                'exc_cls': 'AnalysisError'
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise AnalysisError(error_info['exc_message'])
            
        required_keys = ['missing_skills', 'improvement_suggestions', 'emphasis_suggestions', 'general_suggestions']
        if not all(key in result for key in required_keys):
            error_info = {
                'exc_type': 'AnalysisError',
                'exc_message': "Analysis result missing required fields",
                'exc_module': 'app.tasks',
                'exc_cls': 'AnalysisError'
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise AnalysisError(error_info['exc_message'])
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Applying optimizations...',
                'current': 50,
                'total': 100
            }
        )

        # Normalize resume text before optimization
        try:
            resume_text_normalized = resume_text if isinstance(resume_text, str) else str(resume_text)
            from app.services.ai_analysis import optimize_resume
            optimized_text = optimize_resume(resume_text_normalized, result)
            
            if not optimized_text or not isinstance(optimized_text, str):
                error_info = {
                    'exc_type': 'TypeError',
                    'exc_message': "Optimization failed to produce valid output",
                    'exc_module': 'builtins',
                    'exc_cls': 'TypeError'
                }
                self.update_state(state='FAILURE', meta=error_info)
                raise TypeError(error_info['exc_message'])
                
        except Exception as optimization_error:
            # Handle optimization errors with proper format
            error_info = {
                'exc_type': type(optimization_error).__name__,
                'exc_message': str(optimization_error),
                'exc_module': optimization_error.__class__.__module__ or 'builtins',
                'exc_cls': optimization_error.__class__.__name__
            }
            self.update_state(state='FAILURE', meta=error_info)
            raise

        # Return complete analysis results
        return {
            'status': 'completed',
            'analysis': result,
            'optimized_text': optimized_text,
            'original_text': resume_text
        }

    except SoftTimeLimitExceeded as e:
        error_info = {
            'exc_type': 'SoftTimeLimitExceeded',
            'exc_message': 'Task timed out - please try again with a shorter text',
            'exc_module': 'celery.exceptions',
            'exc_cls': 'SoftTimeLimitExceeded'
        }
        self.update_state(state='FAILURE', meta=error_info)
        raise SoftTimeLimitExceeded(error_info['exc_message'])
        
    except Exception as e:
        # Ensure all exception fields are set properly
        error_info = {
            'exc_type': type(e).__name__,
            'exc_message': str(e),
            'exc_module': e.__class__.__module__ or 'builtins',
            'exc_cls': e.__class__.__name__
        }
        self.update_state(state='FAILURE', meta=error_info)
        # Return the error info as a dict instead of raising
        # This should prevent the serialization issue
        return error_info