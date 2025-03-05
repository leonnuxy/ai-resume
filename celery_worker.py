import os
from app import create_app
from celery import Celery, signals
from config.settings import Config
from config.celery import CustomRedisBackend
import sys
import traceback

def make_celery(app=None):
    """Create a new Celery object and tie together the Celery config to the app's config."""
    app = app or create_app(Config)
    
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0',
        backend_cls=CustomRedisBackend
    )

    # Update Celery config with any custom settings
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_track_started=True,
        task_soft_time_limit=300,  # 5 minutes
        task_time_limit=600,       # 10 minutes
        worker_max_tasks_per_child=200,
        broker_connection_retry_on_startup=True,
        task_routes={
            'app.tasks.*': {'queue': 'analysis'}
        }
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                try:
                    return self.run(*args, **kwargs)
                except Exception as e:
                    # Get full exception information
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    tb_lines = traceback.format_tb(exc_traceback)
                    
                    # Ensure error info is properly formatted with required fields
                    error_info = {
                        'exc_type': exc_type.__name__,
                        'exc_message': str(exc_value),
                        'exc_module': exc_type.__module__,
                        'exc_cls': exc_type.__name__,
                        'traceback': tb_lines
                    }
                    # Only update state if this is a real task with an id
                    if self.request.id:
                        self.update_state(state='FAILURE', meta=error_info)
                    raise

    celery.Task = ContextTask
    return celery

celery = make_celery()

@signals.task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **other):
    """Handle task failures by ensuring proper error formatting."""
    try:
        # Ensure exception information is properly formatted
        if exception:
            # Format error info with required fields for Celery backend
            error_info = {
                'exc_type': type(exception).__name__,
                'exc_message': str(exception),
                'exc_module': exception.__class__.__module__,
                'exc_cls': exception.__class__.__name__
            }
            
            if einfo:
                error_info['traceback'] = str(einfo)
                
            # Update task state with properly formatted error
            if task_id and sender:
                sender.update_state(
                    task_id=task_id,
                    state='FAILURE',
                    meta=error_info
                )
    except Exception as e:
        # Last resort error logging
        print(f"Error in handle_task_failure: {str(e)}")
        

if __name__ == '__main__':
    celery.start()