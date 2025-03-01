import os
from datetime import timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from werkzeug.utils import secure_filename
from flask_session import Session
from resume_parser import parse_pdf, parse_docx, parse_txt
from job_scraper import extract_job_description, ScrapingError
from tasks import analyze_resume_task  # Or from tasks import ...
from dotenv import load_dotenv
from celery_config import make_celery


# Initialize Flask app
app = Flask(__name__)

# App configuration
load_dotenv()
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_TYPE='filesystem',
    UPLOAD_FOLDER='uploads',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Initialize session
Session(app)

# Flask app configuration
app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
app.config["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

# Create Celery instance using the factory function
celery = make_celery(app)

# Constants
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def make_session_permanent():
    """Make the session permanent before each request."""
    session.permanent = True

@app.route('/')
def index():
    """Render the main upload page."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({"status": "OK"})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and parsing."""
    if 'resume' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))

    file = request.files['resume']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    if not file or not allowed_file(file.filename):
        flash('Invalid file type. Please upload a PDF, DOCX, or TXT file.')
        return redirect(url_for('index'))

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Parse file based on extension
        file_ext = filename.rsplit('.', 1)[1].lower()
        formatting = None

        if file_ext == 'pdf':
            text, formatting = parse_pdf(file_path)
        elif file_ext == 'docx':
            text = parse_docx(file_path)
        elif file_ext == 'txt':
            text = parse_txt(file_path)

        # Update session data
        session.clear()
        session.update({
            'modified_text': text,
            'original_file_type': file_ext,
            'original_filename': filename
        })

        if formatting:
            session['formatting'] = formatting

        # Clean up uploaded file
        os.remove(file_path)

        return render_template('result.html', content=text)

    except Exception:
        flash('Error processing file')
        return redirect(url_for('index'))
@app.route('/optimize', methods=['POST'])
def optimize_resume():
    """Analyze and optimize resume against job description."""
    try:
        job_description = request.form.get('job_description')
        if not job_description:
            return jsonify({'error': 'Missing data', 'message': 'Please provide a job description'}), 400

        # Check if this is an API request
        is_api_request = ('modified_text' not in session or
                         request.headers.get('Accept') == 'application/json')
        if is_api_request:
            resume_text = """
            SKILLS
            • Languages: Python, Java, JavaScript
            • Cloud & DevOps: AWS, Docker, Kubernetes
            • Web Development: React, Node.js, REST APIs

            EXPERIENCE
            Software Engineer | Tech Corp
            • Led development of cloud-based applications
            • Implemented CI/CD pipelines
            """
        else:
            resume_text = session.get('modified_text')

        # Start the asynchronous task
        task = analyze_resume_task.delay(resume_text, job_description)

        # Return a response immediately, including the task ID
        if is_api_request:
          return jsonify({'status': 'processing', 'task_id': task.id}), 202
        else:
          return render_template('processing.html', task_id=task.id)

    except Exception as e:
        error_response = {
            'error': 'Internal server error',
            'message': str(e)
        }
        return jsonify(error_response), 500

@app.route('/fetch_job_description', methods=['POST'])
def fetch_job_description():
    """Fetch job description from URL."""
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        description = extract_job_description(url)
        return jsonify({'description': description})

    except ScrapingError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        return jsonify({'error': 'Failed to fetch job description. Please try again.'}), 500

@app.route('/status/<task_id>')
def task_status(task_id):
    task = analyze_resume_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        # Job has not started yet
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0) if task.info else 0,
            'total': task.info.get('total', 1) if task.info else 1,
            'status': task.info.get('status', '') if task.info else ''
        }
        if task.state == 'SUCCESS': # Check for SUCCESS state
            response['result'] = task.result  # Get the result directly
    else:
        # Something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)