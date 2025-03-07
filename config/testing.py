"""Testing configuration."""

from cachelib.file import FileSystemCache
import os

class TestConfig:
    TESTING = True
    SECRET_KEY = 'test_secret_key'
    UPLOAD_FOLDER = 'test_uploads'
    SESSION_TYPE = FileSystemCache(os.path.join('instance', 'flask_session'))
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'memory://'