import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

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