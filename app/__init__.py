# app/__init__.py
import os
import logging
from flask import Flask
from flask_session import Session
from config.settings import Config
from config.celery import make_celery

# Initialize extensions
sess = Session()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure application
    app.config.from_object(config_class)
    app.config['SESSION_CACHELIB'] = os.path.join('instance', 'flask_session')
    
    # Ensure instance directory exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    sess.init_app(app)
    celery = make_celery(app)
    celery.conf.update(app.config)

    # Configure logging
    if not app.debug:
        logging.basicConfig(
            filename=os.path.join(app.instance_path, 'logs', 'app.log'),
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.analysis import analysis_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)

    return app

celery = make_celery(create_app())  # Ensure the app is passed here as well