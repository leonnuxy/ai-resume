# config/settings.py
import os
from cachelib.file import FileSystemCache

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    SESSION_TYPE = FileSystemCache(os.path.join('instance', 'flask_session'))
    UPLOAD_FOLDER = os.path.join('instance', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'