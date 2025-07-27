from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    campaign_id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(200), nullable=False)
    job_name = db.Column(db.String(100), nullable=False, index=True)
    job_webhook_url = db.Column(db.String(500), nullable=False)
    campaign_description = db.Column(db.Text)
    selected_contacts = db.Column(db.Text)  # JSON array of contact IDs
    total_contacts = db.Column(db.Integer, nullable=False)
    processed_contacts = db.Column(db.Integer, default=0)
    successful_contacts = db.Column(db.Integer, default=0)
    failed_contacts = db.Column(db.Integer, default=0)
    campaign_status = db.Column(db.Enum('draft', 'running', 'completed', 'failed', 'paused', name='campaign_status_enum'), default='draft', index=True)
    execution_start_time = db.Column(db.DateTime)
    execution_end_time = db.Column(db.DateTime)
    created_by = db.Column(db.String(100), nullable=False, index=True)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    campaign_settings = db.Column(db.Text)  # JSON for additional settings
    make_scenario_id = db.Column(db.String(100))
    
    # Relationships
    campaign_results = db.relationship('CampaignResult', backref='campaign', lazy=True)
    sample_requests = db.relationship('SampleRequest', backref='campaign', lazy=True)

    def __repr__(self):
        return f'<Campaign {self.campaign_name} ({self.campaign_id})>'

    def to_dict(self):
        return {
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name,
            'job_name': self.job_name,
            'job_webhook_url': self.job_webhook_url,
            'campaign_description': self.campaign_description,
            'selected_contacts': json.loads(self.selected_contacts) if self.selected_contacts else [],
            'total_contacts': self.total_contacts,
            'processed_contacts': self.processed_contacts,
            'successful_contacts': self.successful_contacts,
            'failed_contacts': self.failed_contacts,
            'campaign_status': self.campaign_status,
            'execution_start_time': self.execution_start_time.isoformat() if self.execution_start_time else None,
            'execution_end_time': self.execution_end_time.isoformat() if self.execution_end_time else None,
            'created_by': self.created_by,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None,
            'campaign_settings': json.loads(self.campaign_settings) if self.campaign_settings else {},
            'make_scenario_id': self.make_scenario_id
        }

    def to_summary_dict(self):
        """Simplified version for list views"""
        return {
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign_name,
            'job_name': self.job_name,
            'campaign_status': self.campaign_status,
            'total_contacts': self.total_contacts,
            'successful_contacts': self.successful_contacts,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'execution_start_time': self.execution_start_time.isoformat() if self.execution_start_time else None,
            'execution_end_time': self.execution_end_time.isoformat() if self.execution_end_time else None
        }

    def get_selected_contact_ids(self):
        """Get list of selected contact IDs"""
        return json.loads(self.selected_contacts) if self.selected_contacts else []

    def set_selected_contact_ids(self, contact_ids):
        """Set selected contact IDs"""
        self.selected_contacts = json.dumps(contact_ids)

    def get_campaign_settings(self):
        """Get campaign settings as dict"""
        return json.loads(self.campaign_settings) if self.campaign_settings else {}

    def set_campaign_settings(self, settings):
        """Set campaign settings"""
        self.campaign_settings = json.dumps(settings)


class CampaignResult(db.Model):
    __tablename__ = 'campaign_results'
    
    result_id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.contact_id'), nullable=False, index=True)
    processing_status = db.Column(db.Enum('pending', 'sent', 'delivered', 'failed', 'bounced', name='processing_status_enum'), default='pending', index=True)
    make_response = db.Column(db.Text)  # JSON response from Make.com
    error_message = db.Column(db.Text)
    sample_requested = db.Column(db.Boolean, default=False, index=True)
    processed_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_timestamp = db.Column(db.DateTime)
    response_data = db.Column(db.Text)  # JSON for additional response data
    
    # Relationships
    sample_requests = db.relationship('SampleRequest', backref='campaign_result', lazy=True)

    def __repr__(self):
        return f'<CampaignResult {self.result_id} - Campaign {self.campaign_id} Contact {self.contact_id}>'

    def to_dict(self):
        return {
            'result_id': self.result_id,
            'campaign_id': self.campaign_id,
            'contact_id': self.contact_id,
            'processing_status': self.processing_status,
            'make_response': json.loads(self.make_response) if self.make_response else {},
            'error_message': self.error_message,
            'sample_requested': self.sample_requested,
            'processed_timestamp': self.processed_timestamp.isoformat() if self.processed_timestamp else None,
            'delivery_timestamp': self.delivery_timestamp.isoformat() if self.delivery_timestamp else None,
            'response_data': json.loads(self.response_data) if self.response_data else {}
        }

    def get_make_response(self):
        """Get Make.com response as dict"""
        return json.loads(self.make_response) if self.make_response else {}

    def set_make_response(self, response):
        """Set Make.com response"""
        self.make_response = json.dumps(response)

    def get_response_data(self):
        """Get response data as dict"""
        return json.loads(self.response_data) if self.response_data else {}

    def set_response_data(self, data):
        """Set response data"""
        self.response_data = json.dumps(data)


class CampaignJob(db.Model):
    __tablename__ = 'campaign_jobs'
    
    job_id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    job_description = db.Column(db.Text)
    webhook_url = db.Column(db.String(500), nullable=False)
    make_scenario_id = db.Column(db.String(100))
    job_parameters = db.Column(db.Text)  # JSON for required parameters
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))

    def __repr__(self):
        return f'<CampaignJob {self.job_name}>'

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'job_name': self.job_name,
            'job_description': self.job_description,
            'webhook_url': self.webhook_url,
            'make_scenario_id': self.make_scenario_id,
            'parameters': json.loads(self.job_parameters) if self.job_parameters else [],
            'is_active': self.is_active,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None,
            'created_by': self.created_by
        }

    def get_job_parameters(self):
        """Get job parameters as list"""
        return json.loads(self.job_parameters) if self.job_parameters else []

    def set_job_parameters(self, parameters):
        """Set job parameters"""
        self.job_parameters = json.dumps(parameters)

