from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from flask import current_app as app
from app.utils.validation import allowed_file
from app.utils.file_handling import save_uploaded_file, parse_uploaded_file
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')

@main_bp.route('/health')
def health_check():
    return jsonify({"status": "OK"})

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing."""
    if 'resume' not in request.files:
        flash('No file selected')
        return redirect(url_for('main.index'))

    file = request.files['resume']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('main.index'))

    if not file or not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.')
        return redirect(url_for('main.index'))

    try:
        filename, file_path = save_uploaded_file(file)
        text, formatting = parse_uploaded_file(file_path, filename)
        
        # Update session data
        session.clear()
        session.update({
            'modified_text': text,
            'original_file_type': os.path.splitext(filename)[1][1:],
            'original_filename': filename,
            'formatting': formatting if formatting else None
        })

        # Clean up uploaded file
        os.remove(file_path)

        return render_template('result.html', content=text)

    except Exception as e:
        app.logger.error(f"File upload error: {str(e)}")
        flash('Error processing file')
        return redirect(url_for('main.index'))