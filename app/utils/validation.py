import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension"""
    if '.' not in filename:
        return False
    try:
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in current_app.config['ALLOWED_EXTENSIONS']
    except (AttributeError, IndexError):
        return False

def validate_resume_text(text: str) -> bool:
    """Validate resume text before processing"""
    if not text or len(text) < 50:
        return False
    if len(text) > 10000:
        return False
    return True

def secure_filename_wrapper(filename: str) -> str:
    """Wrapper for werkzeug's secure_filename"""
    return secure_filename(filename)