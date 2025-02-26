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
    jsonify
)
from werkzeug.utils import secure_filename
from flask_session import Session

# Import from our modules
from resume_parser import parse_pdf, parse_docx, parse_txt
from analysis import analyze_resume_for_job, format_optimization_suggestions
from job_scraper import extract_job_description, ScrapingError

# Initialize Flask app
app = Flask(__name__)

# App configuration
app.secret_key = os.urandom(24)
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_TYPE='filesystem',
    UPLOAD_FOLDER='uploads',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Initialize session
Session(app)

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

@app.route('/health')  # <---  Check this route definition
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
        # if 'modified_text' not in session:  # Comment out session check
        #     flash('No resume available for optimization')
        #     return redirect(url_for('index'))

        job_description = request.form.get('job_description')
        if not job_description:
            # flash('Please provide a job description') # Comment out flash and redirect
            return "Error: Job description is missing.", 400, {'Content-Type': 'text/plain'} # Return error message instead of redirect

        # Get resume text and analyze
        resume_text = session['modified_text'] # Keep this line for now, even if session is not set

        analysis = analyze_resume_for_job(resume_text, job_description) # Keep analysis call
        optimized_content = format_optimization_suggestions(analysis) # Keep formatting

        # Update session
        session.update({
            'job_description': job_description,
            'optimization_analysis': analysis
        })

        return render_template('result.html', # Keep rendering
                            content=resume_text,
                            optimized_content=optimized_content,
                            session_data=dict(session))

    except Exception:
        flash('Error during resume optimization')
        return redirect(url_for('index'))

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

if __name__ == '__main__':
    app.run(debug=False) 