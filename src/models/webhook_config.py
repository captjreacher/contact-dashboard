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
            'is_active': self.is_active,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None
        }

class VerificationJob(db.Model):
    __tablename__ = 'verification_jobs'
    
    job_id = db.Column(db.String(36), primary_key=True)
    contact_ids = db.Column(db.Text, nullable=False)  # JSON array of contact IDs
    webhook_config_id = db.Column(db.String(36), db.ForeignKey('webhook_configs.webhook_id'))
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='verification_job_status_enum'), default='pending')
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed_timestamp = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'contact_ids': json.loads(self.contact_ids) if self.contact_ids else [],
            'webhook_config_id': self.webhook_config_id,
            'status': self.status,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'completed_timestamp': self.completed_timestamp.isoformat() if self.completed_timestamp else None,
            'error_message': self.error_message
        }

class CampaignExecution(db.Model):
    __tablename__ = 'campaign_executions'
    
    execution_id = db.Column(db.String(36), primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False)
    job_id = db.Column(db.String(36), db.ForeignKey('campaign_jobs.job_id'), nullable=False)
    contact_ids = db.Column(db.Text, nullable=False)  # JSON array of contact IDs
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='campaign_execution_status_enum'), default='pending')
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed_timestamp = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'execution_id': self.execution_id,
            'campaign_id': self.campaign_id,
            'job_id': self.job_id,
            'contact_ids': json.loads(self.contact_ids) if self.contact_ids else [],
            'status': self.status,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'completed_timestamp': self.completed_timestamp.isoformat() if self.completed_timestamp else None,
            'error_message': self.error_message
        }


