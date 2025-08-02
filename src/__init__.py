from flask import Flask
from flask_migrate import Migrate
from .webhookconfig import webhookconfig_bp
from src.models.models import db

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contact_dashboard.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = True

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(webhookconfig_bp)

    return app
