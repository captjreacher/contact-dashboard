from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

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

