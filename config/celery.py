# config/celery.py
from celery import Celery
from celery.backends.redis import RedisBackend
from celery.exceptions import ImproperlyConfigured

class CustomRedisBackend(RedisBackend):
    """A custom Redis backend that properly handles exception formatting."""
    
    def mark_as_failure(self, task_id, exc, state, traceback=None):
        """Override mark_as_failure to ensure exception info is properly formatted."""
        try:
            # Ensure exception info is properly structured
            if not isinstance(exc, dict):
                exc_info = {
                    'exc_type': type(exc).__name__,
                    'exc_message': str(exc),
                    'exc_module': exc.__class__.__module__,
                    'exc_cls': exc.__class__.__name__
                }
                if traceback:
                    exc_info['traceback'] = traceback
                exc = exc_info
                
            return super().mark_as_failure(task_id, exc, state, traceback)
        except Exception as e:
            # Last resort: provide minimal exception info
            exc_info = {
                'exc_type': 'UnknownError',
                'exc_message': 'An error occurred during task execution',
                'exc_module': 'app.tasks',
                'exc_cls': 'Exception'
            }
            return super().mark_as_failure(task_id, exc_info, state, traceback)
            
    def exception_to_python(self, exc):
        """Override exception_to_python to handle missing exc_type."""
        if isinstance(exc, dict):
            if 'exc_type' not in exc:
                exc['exc_type'] = 'UnknownError'
                exc['exc_module'] = 'app.tasks'
                exc['exc_cls'] = 'Exception'
                exc['exc_message'] = str(exc.get('exc_message', 'Unknown error occurred'))
        return super().exception_to_python(exc)

def make_celery(app):
    """Create a Celery app with custom backend."""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
        backend_cls=CustomRedisBackend
    )
    celery.conf.update(app.config)
    return celery