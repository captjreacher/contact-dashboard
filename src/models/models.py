from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    contact_id = db.Column(db.Integer, primary_key=True)
    upload_batch_id = db.Column(db.String(36), nullable=False, index=True)
    row_number = db.Column(db.Integer)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email_address = db.Column(db.String(255), nullable=False, index=True)
    phone_number = db.Column(db.String(20))
    company_name = db.Column(db.String(200))
    job_title = db.Column(db.String(100))
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state_province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    validation_status = db.Column(db.Enum('pending', 'valid', 'invalid', 'duplicate', name='validation_status_enum'), default='pending', index=True)
    validation_errors = db.Column(db.Text)
    email_verification_status = db.Column(db.Enum('not_verified', 'valid', 'invalid', 'risky', 'unknown', name='email_verification_status_enum'), default='not_verified', index=True)
    email_verification_date = db.Column(db.DateTime)
    email_verification_details = db.Column(db.Text)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_timestamp = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    custom_field1 = db.Column(db.String(255))
    custom_field2 = db.Column(db.String(255))
    custom_field3 = db.Column(db.String(255))

    def __repr__(self):
        return f'<Contact {self.first_name} {self.last_name} ({self.email_address})>'

    def to_dict(self):
        return {
            'contact_id': self.contact_id,
            'upload_batch_id': self.upload_batch_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_address': self.email_address,
            'phone_number': self.phone_number,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'address': {
                'line1': self.address_line1,
                'line2': self.address_line2,
                'city': self.city,
                'state': self.state_province,
                'postal_code': self.postal_code,
                'country': self.country
            },
            'validation_status': self.validation_status,
            'validation_errors': json.loads(self.validation_errors) if self.validation_errors else [],
            'email_verification_status': self.email_verification_status,
            'email_verification_date': self.email_verification_date.isoformat() if self.email_verification_date else None,
            'email_verification_details': json.loads(self.email_verification_details) if self.email_verification_details else {},
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None,
            'updated_timestamp': self.updated_timestamp.isoformat() if self.updated_timestamp else None,
            'is_active': self.is_active,
            'notes': self.notes,
            'custom_fields': {
                'field1': self.custom_field1,
                'field2': self.custom_field2,
                'field3': self.custom_field3
            }
        }

    def to_summary_dict(self):
        """Simplified version for list views"""
        return {
            'contact_id': self.contact_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_address': self.email_address,
            'phone_number': self.phone_number,
            'company_name': self.company_name,
            'validation_status': self.validation_status,
            'validation_errors': json.loads(self.validation_errors) if self.validation_errors else [],
            'email_verification_status': self.email_verification_status,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None
        }


class UploadBatch(db.Model):
    __tablename__ = 'upload_batches'
    
    batch_id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    total_records = db.Column(db.Integer, nullable=False)
    valid_records = db.Column(db.Integer, default=0)
    invalid_records = db.Column(db.Integer, default=0)
    duplicate_records = db.Column(db.Integer, default=0)
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processing_status = db.Column(db.Enum('uploading', 'processing', 'completed', 'failed', name='processing_status_enum'), default='uploading', index=True)
    processing_errors = db.Column(db.Text)
    uploaded_by = db.Column(db.String(100))
    validation_rules_applied = db.Column(db.Text)

    def __repr__(self):
        return f'<UploadBatch {self.filename} ({self.batch_id})>'

    def to_dict(self):
        return {
            'batch_id': self.batch_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'total_records': self.total_records,
            'valid_records': self.valid_records,
            'invalid_records': self.invalid_records,
            'duplicate_records': self.duplicate_records,
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'processing_status': self.processing_status,
            'processing_errors': json.loads(self.processing_errors) if self.processing_errors else [],
            'uploaded_by': self.uploaded_by,
            'validation_rules_applied': json.loads(self.validation_rules_applied) if self.validation_rules_applied else {}
        }


class ValidationRule(db.Model):
    __tablename__ = 'validation_rules'
    
    rule_id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.Enum('required_field', 'format_validation', 'custom_logic', name='rule_type_enum'), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False, index=True)
    validation_pattern = db.Column(db.String(500))
    error_message = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, index=True)
    rule_order = db.Column(db.Integer, default=0)
    created_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ValidationRule {self.rule_name}>'

    def to_dict(self):
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type,
            'field_name': self.field_name,
            'validation_pattern': self.validation_pattern,
            'error_message': self.error_message,
            'is_active': self.is_active,
            'rule_order': self.rule_order,
            'created_timestamp': self.created_timestamp.isoformat() if self.created_timestamp else None
        }


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


class SampleRequest(db.Model):
    __tablename__ = 'sample_requests'
    
    request_id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.contact_id'), nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.campaign_id'), nullable=False, index=True)
    result_id = db.Column(db.Integer, db.ForeignKey('campaign_results.result_id'), nullable=False)
    request_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    fulfillment_status = db.Column(db.Enum('pending', 'processing', 'shipped', 'delivered', 'cancelled', name='fulfillment_status_enum'), default='pending', index=True)
    fulfillment_notes = db.Column(db.Text)
    shipped_date = db.Column(db.DateTime, index=True)
    tracking_number = db.Column(db.String(100))
    shipping_carrier = db.Column(db.String(50))
    fulfilled_by = db.Column(db.String(100))
    fulfillment_cost = db.Column(db.Numeric(10, 2))
    sample_type = db.Column(db.String(100))
    quantity_requested = db.Column(db.Integer, default=1)
    quantity_shipped = db.Column(db.Integer)
    shipping_address = db.Column(db.Text)  # JSON formatted address

    def __repr__(self):
        return f'<SampleRequest {self.request_id} - Contact {self.contact_id}>'

    def to_dict(self):
        return {
            'request_id': self.request_id,
            'contact_id': self.contact_id,
            'campaign_id': self.campaign_id,
            'result_id': self.result_id,
            'request_timestamp': self.request_timestamp.isoformat() if self.request_timestamp else None,
            'fulfillment_status': self.fulfillment_status,
            'fulfillment_notes': self.fulfillment_notes,
            'shipped_date': self.shipped_date.isoformat() if self.shipped_date else None,
            'tracking_number': self.tracking_number,
            'shipping_carrier': self.shipping_carrier,
            'fulfilled_by': self.fulfilled_by,
            'fulfillment_cost': float(self.fulfillment_cost) if self.fulfillment_cost else None,
            'sample_type': self.sample_type,
            'quantity_requested': self.quantity_requested,
            'quantity_shipped': self.quantity_shipped,
            'shipping_address': json.loads(self.shipping_address) if self.shipping_address else {}
        }

    def to_summary_dict(self):
        """Simplified version for list views"""
        return {
            'request_id': self.request_id,
            'contact_id': self.contact_id,
            'campaign_id': self.campaign_id,
            'request_timestamp': self.request_timestamp.isoformat() if self.request_timestamp else None,
            'fulfillment_status': self.fulfillment_status,
            'sample_type': self.sample_type,
            'quantity_requested': self.quantity_requested,
            'shipped_date': self.shipped_date.isoformat() if self.shipped_date else None,
            'tracking_number': self.tracking_number
        }

    def get_shipping_address(self):
        """Get shipping address as dict"""
        return json.loads(self.shipping_address) if self.shipping_address else {}

    def set_shipping_address(self, address):
        """Set shipping address"""
        self.shipping_address = json.dumps(address)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    log_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), index=True)
    action_type = db.Column(db.String(50), nullable=False, index=True)
    table_name = db.Column(db.String(50), index=True)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    def __repr__(self):
        return f'<AuditLog {self.log_id} - {self.action_type} on {self.table_name}>'

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'old_values': json.loads(self.old_values) if self.old_values else {},
            'new_values': json.loads(self.new_values) if self.new_values else {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

    def get_old_values(self):
        """Get old values as dict"""
        return json.loads(self.old_values) if self.old_values else {}

    def set_old_values(self, values):
        """Set old values"""
        self.old_values = json.dumps(values)

    def get_new_values(self):
        """Get new values as dict"""
        return json.loads(self.new_values) if self.new_values else {}

    def set_new_values(self, values):
        """Set new values"""
        self.new_values = json.dumps(values)

    @staticmethod
    def log_action(user_id, action_type, table_name, record_id=None, old_values=None, new_values=None, ip_address=None, user_agent=None):
        """Helper method to create audit log entries"""
        log_entry = AuditLog(
            user_id=user_id,
            action_type=action_type,
            table_name=table_name,
            record_id=record_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if old_values:
            log_entry.set_old_values(old_values)
        if new_values:
            log_entry.set_new_values(new_values)
            
        db.session.add(log_entry)
        return log_entry


# Add relationships after all models are defined
Contact.campaign_results = db.relationship('CampaignResult', backref='contact', lazy=True)
Contact.sample_requests = db.relationship('SampleRequest', backref='contact', lazy=True)
Campaign.campaign_results = db.relationship('CampaignResult', backref='campaign', lazy=True)
Campaign.sample_requests = db.relationship('SampleRequest', backref='campaign', lazy=True)
CampaignResult.sample_requests = db.relationship('SampleRequest', backref='campaign_result', lazy=True)

