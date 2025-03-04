from flask import Blueprint, request, jsonify, session, current_app as app
from app.utils.validation import validate_resume_text
from app.services.job_scraper import extract_job_description, ScrapingError
from app.services.ai_analysis import analyze_resume_for_job  # Ensure this import is correct
from app.tasks import analyze_resume_task
import json

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/optimize', methods=['POST'])
def optimize_resume():
    """Analyze and optimize resume against job description."""
    try:
        job_description = request.form.get('job_description')
        resume_text = session.get('modified_text', '')
        
        if not validate_resume_text(resume_text) or not job_description.strip():
            return jsonify({'error': 'Invalid input data'}), 400

        # Start the asynchronous task
        task = analyze_resume_task.delay(resume_text, job_description)
        return jsonify({'task_id': task.id}), 202

    except Exception as e:
        app.logger.error(f"Optimization error: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500

@analysis_bp.route('/fetch_job_description', methods=['POST'])
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
    except Exception as e:
        app.logger.error(f"Job fetch error: {str(e)}")
        return jsonify({'error': 'Failed to fetch job description'}), 500