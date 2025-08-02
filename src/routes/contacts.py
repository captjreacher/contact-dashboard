from flask import Blueprint, request, jsonify
from src.models.models import db
from src.models.models import Contact, UploadBatch
from src.models.models import AuditLog
from datetime import datetime
import json
import uuid

contacts_bp = Blueprint('contacts', __name__)

@contacts_bp.route('/contacts', methods=['GET', 'POST'])
def handle_contacts():
    if request.method == 'POST':
        return create_contact()
    return get_contacts()

def create_contact():
    """Create a new contact"""
    try:
        data = request.get_json()
        if not data or not data.get('email_address') or not data.get('first_name') or not data.get('last_name'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400

        # Check for existing contact with the same email
        if Contact.query.filter_by(email_address=data['email_address'].lower().strip()).first():
            return jsonify({'success': False, 'error': 'Contact with this email already exists'}), 409

        new_contact = Contact(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email_address=data['email_address'].lower().strip(),
            phone_number=data.get('phone_number'),
            company_name=data.get('company_name'),
            job_title=data.get('job_title'),
            upload_batch_id=str(uuid.uuid4()),  # Assign a unique batch ID for manually added contacts
            validation_status='valid', # Manually added contacts are considered valid
            email_verification_status='not_verified'
        )

        db.session.add(new_contact)
        db.session.commit()

        # Log the creation
        AuditLog.log_action(
            user_id='system',  # TODO: Get from session
            action_type='create',
            table_name='contacts',
            record_id=new_contact.contact_id,
            new_values=new_contact.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'contact': new_contact.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_contacts():
    """Retrieve contacts with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        validation_status = request.args.get('validation_status')
        verification_status = request.args.get('verification_status')
        batch_id = request.args.get('batch_id')
        sort_by = request.args.get('sort_by', 'created_timestamp')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Contact.query.filter_by(is_active=True)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Contact.first_name.ilike(search_term),
                    Contact.last_name.ilike(search_term),
                    Contact.email_address.ilike(search_term),
                    Contact.company_name.ilike(search_term)
                )
            )
        
        if validation_status:
            query = query.filter_by(validation_status=validation_status)
        
        if verification_status:
            query = query.filter_by(email_verification_status=verification_status)
        
        if batch_id:
            query = query.filter_by(upload_batch_id=batch_id)
        
        # Apply sorting
        if hasattr(Contact, sort_by):
            sort_column = getattr(Contact, sort_by)
            if sort_order == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
        # Paginate results
        contacts = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'total_contacts': contacts.total,
            'page': page,
            'per_page': per_page,
            'total_pages': contacts.pages,
            'contacts': [contact.to_summary_dict() for contact in contacts.items]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Get detailed contact information"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Get campaign history
        from src.models.models import CampaignResult, Campaign
        campaign_results = db.session.query(CampaignResult, Campaign).join(
            Campaign, CampaignResult.campaign_id == Campaign.campaign_id
        ).filter(CampaignResult.contact_id == contact_id).all()
        
        campaign_history = []
        for result, campaign in campaign_results:
            campaign_history.append({
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name,
                'sent_date': result.processed_timestamp.isoformat() if result.processed_timestamp else None,
                'status': result.processing_status
            })
        
        # Get sample requests
        sample_requests = []
        for sample in contact.sample_requests:
            sample_requests.append({
                'request_id': sample.request_id,
                'campaign_id': sample.campaign_id,
                'request_date': sample.request_timestamp.isoformat() if sample.request_timestamp else None,
                'fulfillment_status': sample.fulfillment_status
            })
        
        contact_dict = contact.to_dict()
        contact_dict['campaign_history'] = campaign_history
        contact_dict['sample_requests'] = sample_requests
        
        return jsonify({
            'success': True,
            'contact': contact_dict
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Update contact information"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        data = request.get_json()
        
        # Store old values for audit
        old_values = contact.to_dict()
        
        # Update fields
        if 'first_name' in data:
            contact.first_name = data['first_name']
        if 'last_name' in data:
            contact.last_name = data['last_name']
        if 'email_address' in data:
            contact.email_address = data['email_address'].lower().strip()
        if 'phone_number' in data:
            contact.phone_number = data['phone_number']
        if 'company_name' in data:
            contact.company_name = data['company_name']
        if 'job_title' in data:
            contact.job_title = data['job_title']
        
        # Update address
        if 'address' in data:
            address = data['address']
            contact.address_line1 = address.get('line1')
            contact.address_line2 = address.get('line2')
            contact.city = address.get('city')
            contact.state_province = address.get('state')
            contact.postal_code = address.get('postal_code')
            contact.country = address.get('country')
        
        if 'notes' in data:
            contact.notes = data['notes']
        
        contact.updated_timestamp = datetime.utcnow()
        
        # Re-validate if email changed
        if 'email_address' in data:
            contact.email_verification_status = 'not_verified'
            contact.email_verification_date = None
            contact.email_verification_details = None
        
        db.session.commit()
        
        # Log the update
        AuditLog.log_action(
            user_id='system',  # TODO: Get from session
            action_type='update',
            table_name='contacts',
            record_id=contact_id,
            old_values=old_values,
            new_values=contact.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contact': contact.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Soft delete contact"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Soft delete
        contact.is_active = False
        contact.updated_timestamp = datetime.utcnow()
        
        db.session.commit()
        
        # Log the deletion
        AuditLog.log_action(
            user_id='system',  # TODO: Get from session
            action_type='delete',
            table_name='contacts',
            record_id=contact_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/verify', methods=['POST'])
def start_email_verification():
    """Start email verification for selected contacts"""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])
        verification_options = data.get('verification_options', {})
        
        if not contact_ids:
            return jsonify({'success': False, 'error': 'No contacts selected'}), 400
        
        # Get contacts
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()
        
        if not contacts:
            return jsonify({'success': False, 'error': 'No valid contacts found'}), 404
        
        # Generate verification job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # In a real application, this would trigger an asynchronous job
        # For now, we'll simulate email verification
        for contact in contacts:
            # Simulate verification logic
            email = contact.email_address
            
            # Simple validation - check if email has valid format and common domains
            if '@gmail.com' in email or '@yahoo.com' in email or '@outlook.com' in email:
                verification_status = 'valid'
                verification_details = {
                    'deliverable': True,
                    'risk_level': 'low',
                    'provider': email.split('@')[1]
                }
            elif '@test.com' in email or '@example.com' in email:
                verification_status = 'invalid'
                verification_details = {
                    'deliverable': False,
                    'risk_level': 'high',
                    'provider': email.split('@')[1]
                }
            else:
                verification_status = 'unknown'
                verification_details = {
                    'deliverable': None,
                    'risk_level': 'medium',
                    'provider': email.split('@')[1]
                }
            
            contact.email_verification_status = verification_status
            contact.email_verification_date = datetime.utcnow()
            contact.email_verification_details = json.dumps(verification_details)
            contact.updated_timestamp = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'verification_job_id': job_id,
            'total_contacts': len(contacts),
            'estimated_completion': datetime.utcnow().isoformat(),
            'status': 'completed'  # Since we're processing synchronously
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/verify/<job_id>/status', methods=['GET'])
def get_verification_status(job_id):
    """Check email verification progress"""
    try:
        # Since we process synchronously, always return completed
        # In a real application, you'd track job status in the database
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'completed',
            'progress': {
                'total_contacts': 0,  # Would be tracked in job record
                'processed_contacts': 0,
                'valid_emails': 0,
                'invalid_emails': 0,
                'risky_emails': 0
            },
            'completion_time': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/stats', methods=['GET'])
def get_contact_stats():
    """Get contact statistics"""
    try:
        total_contacts = Contact.query.filter_by(is_active=True).count()
        valid_contacts = Contact.query.filter_by(is_active=True, validation_status='valid').count()
        invalid_contacts = Contact.query.filter_by(is_active=True, validation_status='invalid').count()
        duplicate_contacts = Contact.query.filter_by(is_active=True, validation_status='duplicate').count()
        
        verified_emails = Contact.query.filter_by(is_active=True, email_verification_status='valid').count()
        unverified_emails = Contact.query.filter_by(is_active=True, email_verification_status='not_verified').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_contacts': total_contacts,
                'valid_contacts': valid_contacts,
                'invalid_contacts': invalid_contacts,
                'duplicate_contacts': duplicate_contacts,
                'verified_emails': verified_emails,
                'unverified_emails': unverified_emails
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_bp.route('/contacts/export', methods=['GET'])
def export_contacts():
    """Export contacts to CSV"""
    try:
        # Get filter parameters
        validation_status = request.args.get('validation_status')
        verification_status = request.args.get('verification_status')
        batch_id = request.args.get('batch_id')
        
        # Build query
        query = Contact.query.filter_by(is_active=True)
        
        if validation_status:
            query = query.filter_by(validation_status=validation_status)
        
        if verification_status:
            query = query.filter_by(email_verification_status=verification_status)
        
        if batch_id:
            query = query.filter_by(upload_batch_id=batch_id)
        
        contacts = query.all()
        
        # Convert to CSV format
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Contact ID', 'First Name', 'Last Name', 'Email Address', 'Phone Number',
            'Company Name', 'Job Title', 'Address Line 1', 'Address Line 2',
            'City', 'State/Province', 'Postal Code', 'Country',
            'Validation Status', 'Email Verification Status', 'Created Date'
        ])
        
        # Write data
        for contact in contacts:
            writer.writerow([
                contact.contact_id,
                contact.first_name,
                contact.last_name,
                contact.email_address,
                contact.phone_number,
                contact.company_name,
                contact.job_title,
                contact.address_line1,
                contact.address_line2,
                contact.city,
                contact.state_province,
                contact.postal_code,
                contact.country,
                contact.validation_status,
                contact.email_verification_status,
                contact.created_timestamp.strftime('%Y-%m-%d %H:%M:%S') if contact.created_timestamp else ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=contacts_export.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

