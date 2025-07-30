from src.models.models import db
from datetime import datetime
import json

class WebhookConfig(db.Model):
    __tablename__ = 'webhook_configs'
    
    webhook_id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    webhook_type = db.Column(db.Enum('verification', 'campaign', name='webhook_type_enum'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    input_fields = db.Column(db.Text)  # JSON string of field definitions
    output_fields = db.Column(db.Text)  # JSON string of field definitions
    headers = db.Column(db.Text)  # JSON string of headers
    header_name = db.Column(db.String(255))  # New field for header name
    header_value = db.Column(db.Text)  # New field for header value
    is_active = db.Column(db.Boolean, default=True)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'webhook_id': self.webhook_id,
            'name': self.name,
            'description': self.description,
            'webhook_type': self.webhook_type,
            'url': self.url,
            'input_fields': self.input_fields,
            'output_fields': self.output_fields,
            'headers': self.headers,
            'header_name': self.header_name,
            'header_value': self.header_value,
            'is_active': self.is_active,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None
        }