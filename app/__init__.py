# app/__init__.py
import os
import logging
from flask import Flask, session, jsonify, request
from flask_session import Session
from datetime import timedelta
from config.settings import Config
from config.celery import make_celery

# Initialize extensions
sess = Session()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure application
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join('instance', 'flask_session')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Session timeout
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'instance/uploads'
    app.config['SERVER_NAME'] = '127.0.0.1:5000'  # Set server name explicitly
    
    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.before_request
    def make_session_permanent():
        session.permanent = True
        
    @app.after_request
    def after_request(response):
        # Ensure session data is saved after each request
        if hasattr(session, 'modified') and session.modified:
            app.logger.debug(f"Session data modified: {dict(session)}")
        return response

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle bad request errors."""
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': str(error),
                'message': 'Invalid request. Please check your input.'
            }), 400
        flash('Invalid request. Please check your input.')
        return redirect(url_for('main.index'))

    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors."""
        app.logger.error(f'Server Error: {str(error)}', exc_info=True)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred. Please try again.'
            }), 500
        flash('An unexpected error occurred. Please try again.')
        return redirect(url_for('main.index'))

    @app.errorhandler(408)
    def timeout_error(error):
        """Handle request timeout errors."""
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'error': 'Request timed out',
                'message': 'The analysis took too long to complete. Please try with shorter content.'
            }), 408
        flash('The analysis took too long to complete. Please try with shorter content.')
        return redirect(url_for('main.index'))

    # Initialize extensions with app
    sess.init_app(app)
    celery = make_celery(app)
    celery.conf.update(app.config)

    # Configure logging
    if not app.debug:
        log_dir = os.path.join(app.instance_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, 'app.log'),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Register blueprints with explicit URL prefixes
    from app.routes import main, analysis
    app.register_blueprint(main.main_bp, url_prefix='/')  # Mount main routes at root
    app.register_blueprint(analysis.analysis_bp, url_prefix='/analysis')

    return app

# Create the celery instance
celery = make_celery(create_app())