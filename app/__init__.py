import os
from flask import Flask, jsonify
from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf
from app import models

def create_app(config_name=None):
    """Application factory for the Seminar Hall Management System."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Validate database connection string early
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError(
            "DATABASE_URL is not set. Please ensure you have created a .env file "
            "with a valid MySQL connection string (refer to .env.example)."
        )

    # Initialize extensions with app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Setup User loader for Flask-Login (tied to UserModel in future steps)
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Basic root health check route for initial environment verification
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'application': 'Seminar Hall Management System (SHMS)',
            'environment': config_name
        }), 200


    # Register the application's existing route blueprints
    from app.routes import (
        main_bp,
        auth_bp,
        faculty_bp,
        principal_bp,
        admin_bp,
        api_bp,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(principal_bp, url_prefix='/principal')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
