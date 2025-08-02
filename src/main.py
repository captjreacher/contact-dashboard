import os
import sys

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from src.models.models import db, Contact, UploadBatch, ValidationRule, Campaign, CampaignResult, CampaignJob, SampleRequest, AuditLog
from src.models import WebhookConfig
from src.routes.user import user_bp
from src.routes.upload import upload_bp
from src.routes.contacts import contacts_bp
from src.routes.campaigns import campaigns_bp
from src.routes.samples import samples_bp
from src.routes.webhooks import webhooks_bp
from src.routes.settings import settings_bp
from src.routes.verification import verification_bp
from sqlalchemy.orm import scoped_session, sessionmaker

# Initialize Flask app with the correct static folder for the React build
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Enable CORS
CORS(app, origins="*")

# Database config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", "app.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Create the database if it doesn't exist
with app.app_context():
    db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db.create_all()

# Register Blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(campaigns_bp, url_prefix='/api')
app.register_blueprint(samples_bp, url_prefix='/api')
app.register_blueprint(webhooks_bp, url_prefix='/api')
app.register_blueprint(settings_bp, url_prefix='/api/settings')
app.register_blueprint(verification_bp, url_prefix='/api/verification')

# Import and register Notion blueprint
from src.routes.notion import notion_bp
app.register_blueprint(notion_bp)

# Catch-all route to serve index.html for front-end routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

# Clean up DB sessions
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

# Enable debug mode explicitly
app.debug = True

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

