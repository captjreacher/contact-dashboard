import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.models import db, Contact, UploadBatch, ValidationRule, Campaign, CampaignResult, CampaignJob, SampleRequest, AuditLog
from src.routes.user import user_bp
from src.routes.upload import upload_bp
from src.routes.contacts import contacts_bp
from src.routes.campaigns import campaigns_bp
from src.routes.samples import samples_bp
from src.routes.webhooks import webhooks_bp
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Enable CORS for all routes
CORS(app, origins="*")

# Register all blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(upload_bp, url_prefix='/api')
app.register_blueprint(contacts_bp, url_prefix='/api')
app.register_blueprint(campaigns_bp, url_prefix='/api')
app.register_blueprint(samples_bp, url_prefix='/api')
app.register_blueprint(webhooks_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database/app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Create the database directory if it doesn't exist
    db_dir = os.path.join(os.path.dirname(__file__), 'database')
    os.makedirs(db_dir, exist_ok=True)
    db.create_all()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
