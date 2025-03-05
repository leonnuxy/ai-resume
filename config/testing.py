"""Testing configuration."""

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test_secret_key'
    UPLOAD_FOLDER = 'test_uploads'
    SESSION_TYPE = 'filesystem'
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'memory://'