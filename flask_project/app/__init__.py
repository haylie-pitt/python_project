from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt  # Importing Flask-Bcrypt

# Initialize db and migration tools globally
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()  # Initialize Bcrypt for password hashing

def create_app():
    app = Flask(__name__)

    # Set the SECRET_KEY for session management
    app.config['SECRET_KEY'] = 'your_unique_and_secret_key_here'  # Make sure to replace this with a secure key

    # Load app configuration from 'config.Config'
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)  # Initialize bcrypt with the app

    # Import models AFTER initializing the app and db
    with app.app_context():
        from .models import Account, Event, EventAttendance

    # Register blueprints
    from .views import main_bp
    app.register_blueprint(main_bp)

    return app