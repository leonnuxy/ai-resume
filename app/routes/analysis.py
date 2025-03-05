from flask import Blueprint, request, jsonify, session, current_app as app, redirect, url_for, render_template, flash
from app.utils.validation import validate_resume_text
from app.services.job_scraper import extract_job_description, ScrapingError
from app.services.ai_analysis import analyze_resume_for_job, test_ollama_connection
from app.tasks import analyze_resume_task, celery
from celery.exceptions import TimeoutError
import json
import time

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

@analysis_bp.route('/test_ollama')
def test_ollama():
    """Test the connection to Ollama service."""
    try:
        is_connected = test_ollama_connection()
        return jsonify({'connected': is_connected})
    except Exception as e:
        app.logger.error(f"Ollama connection test error: {str(e)}")
        return jsonify({'error': 'Failed to test Ollama connection'}), 500

@analysis_bp.route('/optimize', methods=['POST'])
def optimize_resume():
    """Analyze and optimize resume against job description."""
    try:
        # Get and validate inputs
        job_description = request.form.get('job_description', '').strip()
        resume_text = session.get('modified_text', '').strip()
        
        # Debug logging
        app.logger.info(f"Processing request with session ID: {session.get('_id', 'No ID')}")
        app.logger.info(f"Job Description Length: {len(job_description)}")
        app.logger.info(f"Resume Text Length: {len(resume_text)}")
        
        # Input validation with detailed error messages
        validation_errors = []
        
        if not resume_text:
            validation_errors.append("Resume text is missing. Please upload or paste your resume.")
        elif len(resume_text) < 100:
            validation_errors.append("Resume is too short (minimum 100 characters needed).")
            
        if not job_description:
            validation_errors.append("Job description is missing. Please provide job requirements.")
        elif len(job_description) < 50:
            validation_errors.append("Job description is too short (minimum 50 characters needed).")
            
        # Check for basic resume structure
        resume_keywords = ['experience', 'education', 'skills', 'work', 'job', 'project']
        if not any(keyword in resume_text.lower() for keyword in resume_keywords):
            validation_errors.append("Resume appears to be missing standard sections (Experience, Education, Skills, etc).")
            
        if validation_errors:
            error_msg = " ".join(validation_errors)
            app.logger.warning(f"Validation failed: {error_msg}")
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'error': error_msg}), 400
            flash(error_msg)
            return redirect(url_for('main.index'))

        # Save current task details in session
        task = analyze_resume_task.delay(resume_text, job_description)
        session['current_task'] = {
            'id': task.id,
            'start_time': time.time(),
            'resume_length': len(resume_text),
            'job_desc_length': len(job_description)
        }
        session.modified = True
        
        # Return response based on content type
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'task_id': task.id,
                'message': 'Analysis started successfully'
            }), 202
        
        return render_template('processing.html', task_id=task.id)
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': error_msg}), 500
        flash('Error processing request. Please try again.')
        return redirect(url_for('main.index'))

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

@analysis_bp.route('/status/<task_id>')
def get_task_status(task_id):
    """Get the status of a background task."""
    try:
        task = celery.AsyncResult(task_id)
        
        # Handle case where task state can't be decoded
        try:
            current_state = task.state
        except ValueError:
            error_info = {
                'exc_type': 'TaskStateError',
                'exc_message': 'Unable to decode task state',
                'exc_module': 'app.routes.analysis',
                'exc_cls': 'TaskStateError'
            }
            return jsonify({
                'state': 'FAILURE',
                'status': error_info['exc_message'],
                'error': error_info
            })

        if current_state == 'PENDING':
            response = {
                'state': current_state,
                'status': 'Task is pending...'
            }
        elif current_state == 'FAILURE':
            # Extract error information from task.info if available
            error_info = task.info
            if isinstance(error_info, Exception):
                error_info = {
                    'exc_type': type(error_info).__name__,
                    'exc_message': str(error_info),
                    'exc_module': error_info.__class__.__module__,
                    'exc_cls': error_info.__class__.__name__
                }
            elif not isinstance(error_info, dict) or 'exc_type' not in error_info:
                error_info = {
                    'exc_type': 'TaskError',
                    'exc_message': str(error_info) if error_info else 'Unknown error occurred',
                    'exc_module': 'app.routes.analysis',
                    'exc_cls': 'TaskError'
                }
            
            response = {
                'state': current_state,
                'status': error_info.get('exc_message', 'Task failed'),
                'error': error_info
            }
        else:
            if task.info:
                if isinstance(task.info, dict):
                    if 'status' in task.info:  # Progress update
                        response = {
                            'state': current_state,
                            'chunk': json.dumps(task.info)
                        }
                    else:  # Final result
                        response = {
                            'state': current_state,
                            'chunk': json.dumps({
                                'status': 'completed',
                                'result': task.info.get('analysis', {}),
                                'optimized_text': task.info.get('optimized_text', ''),
                                'original_text': task.info.get('original_text', '')
                            })
                        }
                else:
                    response = {
                        'state': current_state,
                        'status': str(task.info)
                    }
            else:
                response = {
                    'state': current_state,
                    'chunk': json.dumps({
                        'status': 'Processing...'
                    })
                }
        
        return jsonify(response)
    except TimeoutError:
        error_info = {
            'exc_type': 'TimeoutError',
            'exc_message': 'Request timed out',
            'exc_module': 'celery.exceptions',
            'exc_cls': 'TimeoutError'
        }
        return jsonify({
            'state': 'FAILURE',
            'status': 'Request timed out',
            'error': error_info
        }), 408
    except Exception as e:
        app.logger.error(f"Error in get_task_status: {str(e)}", exc_info=True)
        error_info = {
            'exc_type': type(e).__name__,
            'exc_message': str(e),
            'exc_module': e.__class__.__module__,
            'exc_cls': e.__class__.__name__
        }
        return jsonify({
            'state': 'FAILURE',
            'status': str(e),
            'error': error_info
        }), 500