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
        max_wait_time = 600  # 10 minutes maximum wait time
        start_time = time.time()
        
        response = {
            'state': task.state,
        }
        
        # Check if task has been running too long
        if task.state == 'PROGRESS' and task.info:
            current_time = time.time()
            if task.info.get('start_time') and (current_time - task.info['start_time']) > max_wait_time:
                task.revoke(terminate=True)
                return jsonify({
                    'state': 'FAILURE',
                    'status': 'Task terminated due to timeout',
                    'chunk': json.dumps({
                        'status': 'error',
                        'message': 'Analysis took too long to complete',
                        'details': 'Please try with shorter content'
                    })
                }), 408
        
        if task.state == 'PENDING':
            response.update({
                'status': 'Task is pending...',
                'chunk': json.dumps({
                    'status': 'pending',
                    'message': 'Starting analysis...'
                })
            })
        elif task.state == 'FAILURE':
            error_info = task.info or {}
            error_type = error_info.get('error_type', 'unknown_error')
            error_msg = error_info.get('exc_message', 'Task failed')
            
            error_details = {
                'timeout': 'The analysis took too long. Try with shorter content.',
                'validation_error': 'Please check your input and try again.',
                'analysis_error': 'Analysis failed. Please try again.',
                'unknown_error': 'An unexpected error occurred.'
            }
            
            response.update({
                'status': error_msg,
                'error': error_msg,
                'chunk': json.dumps({
                    'status': 'error',
                    'message': error_msg,
                    'details': error_details.get(error_type, 'Please try again'),
                    'error_type': error_type
                })
            })
            return jsonify(response), 500
            
        elif task.state == 'SUCCESS':
            if not task.result:
                return jsonify({
                    'state': 'FAILURE',
                    'status': 'No analysis results received',
                    'chunk': json.dumps({
                        'status': 'error',
                        'message': 'No analysis results received',
                        'details': 'Please try again'
                    })
                }), 500
            
            # Handle successful result
            result = task.result.get('result', {})
            if not isinstance(result, dict):
                app.logger.error(f"Invalid result format: {result}")
                return jsonify({
                    'state': 'FAILURE',
                    'status': 'Invalid analysis format',
                    'chunk': json.dumps({
                        'status': 'error',
                        'message': 'Invalid analysis format received',
                        'details': 'The analysis result was not in the expected format'
                    })
                }), 500
            
            # Check for required sections
            required_keys = ['missing_skills', 'improvement_suggestions', 'emphasis_suggestions', 'general_suggestions']
            if not all(key in result for key in required_keys):
                app.logger.error(f"Missing required sections in result: {result.keys()}")
                return jsonify({
                    'state': 'FAILURE',
                    'status': 'Incomplete analysis results',
                    'chunk': json.dumps({
                        'status': 'error',
                        'message': 'Incomplete analysis results',
                        'details': 'The analysis is missing some required sections'
                    })
                }), 500
            
            response['chunk'] = json.dumps({
                'status': 'completed',
                'result': result,
                'execution_time': time.time() - start_time
            })
            
        elif task.state == 'PROGRESS':
            if task.info:
                response['chunk'] = json.dumps({
                    'status': 'in_progress',
                    'current': task.info.get('current', 0),
                    'total': task.info.get('total', 100),
                    'status_message': task.info.get('status', 'Processing...'),
                    'execution_time': time.time() - task.info.get('start_time', start_time)
                })
        
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Failed to check task status: {str(e)}", exc_info=True)
        return jsonify({
            'state': 'FAILURE',
            'status': 'Failed to check task status',
            'chunk': json.dumps({
                'status': 'error',
                'message': 'Failed to check analysis status',
                'details': 'An unexpected error occurred. Please try again.'
            })
        }), 500