from flask import Blueprint, render_template, redirect, request, url_for, flash, session, jsonify
from flask import current_app as app
from app.utils.validation import allowed_file
from app.utils.file_handling import save_uploaded_file, parse_uploaded_file
from app.services.ai_analysis import analyze_document_structure  # Updated import path
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main upload page."""
    # Store example resume text in session for testing
    if 'modified_text' not in session:
        session['modified_text'] = """John Doe
        Senior Software Engineer

        SUMMARY
        Experienced software engineer with 6+ years of expertise in full-stack development,
        cloud architectures, and team leadership. Proven track record of delivering scalable solutions
        and driving technical innovation.

        SKILLS
        • Programming: Python, JavaScript, TypeScript, Java
        • Cloud & DevOps: AWS, Docker, Kubernetes, CI/CD
        • Web Technologies: React, Node.js, REST APIs
        • Databases: PostgreSQL, MongoDB
        • Leadership: Team Management, Agile/Scrum

        EXPERIENCE
        Senior Software Engineer | TechCorp Inc.
        2020 - Present
        • Led development of cloud-native applications using AWS and Kubernetes
        • Managed team of 5 developers, improving delivery time by 30%
        • Implemented microservices architecture using Python and Node.js

        Software Engineer | Innovation Labs
        2018 - 2020
        • Developed full-stack web applications using React and Node.js
        • Designed and implemented RESTful APIs serving 1M+ requests daily
        • Optimized database queries, reducing response time by 40%

        EDUCATION
        Bachelor of Science in Computer Science
        Technical University | 2014 - 2018
        """
    return render_template('index.html')

@main_bp.route('/health')
def health_check():
    return jsonify({"status": "OK"})

@main_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing."""
    try:
        # Log session state before processing
        app.logger.info(f"Session before upload: {dict(session)}")
        
        if 'resume' not in request.files:
            app.logger.error("No file part in request")
            flash('No file uploaded')
            return redirect(url_for('main.index'))
        
        file = request.files['resume']
        if not file or not file.filename:
            app.logger.error("No file selected")
            flash('No file selected')
            return redirect(url_for('main.index'))
            
        if not allowed_file(file.filename):
            app.logger.error(f"Invalid file type: {file.filename}")
            flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.')
            return redirect(url_for('main.index'))
            
        filename, file_path = save_uploaded_file(file)
        text, formatting = parse_uploaded_file(file_path, filename)
        
        if not text or len(text.strip()) < 100:
            app.logger.error(f"Parsed text too short or empty: {len(text) if text else 0} chars")
            flash('The uploaded file contains insufficient text content. Please ensure your resume is complete.')
            return redirect(url_for('main.index'))
        
        # Clear and update session with new data
        session.clear()
        session_data = {
            'modified_text': text,
            'original_file_type': os.path.splitext(filename)[1][1:],
            'original_filename': filename,
            'formatting': formatting if formatting else None,
            'upload_timestamp': os.path.getmtime(file_path)
        }
        session.update(session_data)
        
        # Verify session data was stored
        app.logger.info(f"Session after upload: {dict(session)}")
        if 'modified_text' not in session:
            raise ValueError("Failed to store resume text in session")
            
        # Clean up the temporary file
        os.remove(file_path)
        app.logger.info(f"File upload successful: {filename}")
        
        return redirect(url_for('main.processing'))
        
    except Exception as e:
        app.logger.error(f"File upload error: {str(e)}", exc_info=True)
        flash('Error processing file. Please try again.')
        return redirect(url_for('main.index'))

@main_bp.route('/processing')
def processing():
    """Show processing page after successful upload."""
    task_id = request.args.get('task_id')
    
    if task_id:
        return render_template('processing.html', task_id=task_id)
    
    if 'modified_text' not in session:
        return redirect(url_for('main.index'))
        
    return render_template('result.html', content=session['modified_text'])