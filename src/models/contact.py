from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    contact_id = db.Column(db.Integer, primary_key=True)
    upload_batch_id = db.Column(db.String(36), nullable=False, index=True)
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
    
    # Relationships
    campaign_results = db.relationship('CampaignResult', backref='contact', lazy=True)
    sample_requests = db.relationship('SampleRequest', backref='contact', lazy=True)

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

