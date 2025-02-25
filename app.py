import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import timedelta
from flask_session import Session
import io

# Import from our modules
from resume_parser import parse_pdf, parse_docx, parse_txt
from analysis import analyze_resume_for_job, format_optimization_suggestions
from job_scraper import extract_job_description, ScrapingError

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a strong random key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Increase session lifetime
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem to store session data
Session(app)  # Initialize session

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    session.permanent = True
    
    if 'resume' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            file_ext = filename.rsplit('.', 1)[1].lower()
            formatting = None
            
            if file_ext == 'pdf':
                text, formatting = parse_pdf(file_path)
            elif file_ext == 'docx':
                text = parse_docx(file_path)
            elif file_ext == 'txt':
                text = parse_txt(file_path)
            
            # Anonymize personal information in text
            modified_text = text
            
            # Clear and update session data
            session.clear()
            session['modified_text'] = modified_text
            session['original_file_type'] = file_ext
            session['original_filename'] = filename
            if formatting:
                session['formatting'] = formatting
            
            os.remove(file_path)
            
            return render_template('result.html', content=modified_text)
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            flash('Error processing file')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.')
        return redirect(url_for('index'))

@app.route('/check_session')
def check_session():
    return '', 204

@app.route('/optimize', methods=['POST'])
def optimize_resume():
    try:
        if 'modified_text' not in session:
            flash('No resume available for optimization')
            return redirect(url_for('index'))
        
        job_description = request.form.get('job_description')
        if not job_description:
            flash('Please provide a job description')
            return redirect(url_for('result'))
        
        # Get the resume text from session
        resume_text = session['modified_text']
        
        # Analyze resume against job description
        analysis = analyze_resume_for_job(resume_text, job_description)
        
        # Format the suggestions
        optimized_content = format_optimization_suggestions(analysis)
        
        # Store the job description and analysis in session
        session['job_description'] = job_description
        session['optimization_analysis'] = analysis
        
        return render_template('result.html',
                            content=resume_text,
                            optimized_content=optimized_content,
                            session_data=dict(session))
                            
    except Exception as e:
        print(f"Error in optimization: {str(e)}")
        flash('Error during resume optimization')
        return redirect(url_for('index'))

@app.route('/fetch_job_description', methods=['POST'])
def fetch_job_description():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
            
        description = extract_job_description(url)
        return jsonify({'description': description})
        
    except ScrapingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Failed to fetch job description. Please try again.'}), 500

if __name__ == '__main__':
    app.run(debug=False) 