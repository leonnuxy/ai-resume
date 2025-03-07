import os
import pdfplumber
from docx import Document
from flask import current_app as app
from werkzeug.utils import secure_filename
from app.services.resume_parser import parse_pdf, parse_docx, parse_txt

def save_uploaded_file(file) -> tuple:
    """Save uploaded file to instance folder"""
    filename = secure_filename(file.filename)
    upload_folder = os.path.join(app.instance_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return filename, file_path

def parse_uploaded_file(file_path: str, filename: str) -> tuple:
    """Parse file based on its extension"""
    ext = os.path.splitext(filename)[1][1:].lower()
    
    if ext == 'pdf':
        return parse_pdf(file_path)
    elif ext == 'docx':
        return parse_docx(file_path), None
    elif ext == 'txt':
        return parse_txt(file_path), None
    else:
        raise ValueError("Unsupported file type")

def remove_uploaded_file(file_path: str):
    """Safely remove uploaded file"""
    if os.path.exists(file_path):
        os.remove(file_path)