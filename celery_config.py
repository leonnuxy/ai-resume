from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker="redis://localhost:6379/0",  # Force Redis as the broker
        backend="redis://localhost:6379/0"  # Ensure Redis is used for result storage
    )
    celery.conf.update(app.config)
    return celery
