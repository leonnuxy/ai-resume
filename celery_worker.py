import os
from app import create_app
from celery import Celery, signals
from config.settings import Config

def make_celery(app=None):
    """Create a new Celery object and tie together the Celery config to the app's config."""
    app = app or create_app(Config)
    
    celery = Celery(
        app.import_name,
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
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
                    # Ensure error info is properly formatted
                    error_info = {
                        'exc_type': e.__class__.__name__,
                        'exc_message': str(e),
                        'error_type': getattr(e, 'error_type', 'unknown_error')
                    }
                    self.update_state(state='FAILURE', meta=error_info)
                    raise

    celery.Task = ContextTask
    return celery

celery = make_celery()

@signals.task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Handle task failures by ensuring proper error formatting."""
    error_info = {
        'exc_type': exception.__class__.__name__,
        'exc_message': str(exception),
        'error_type': getattr(exception, 'error_type', 'unknown_error')
    }
    sender.update_state(task_id=task_id, state='FAILURE', meta=error_info)

if __name__ == '__main__':
    celery.start()