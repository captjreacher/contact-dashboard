from flask import Blueprint, request, jsonify
import uuid
import json
import requests
from datetime import datetime
from src.models.models import db, Contact
from src.models.webhook_config import WebhookConfig, VerificationJob

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/run', methods=['POST'])
def run_verification():
    """Start email verification for selected contacts"""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])
        
        if not contact_ids:
            return jsonify({'error': 'No contacts selected for verification'}), 400
        
        # Validate that all contact IDs exist
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()
        if len(contacts) != len(contact_ids):
            return jsonify({'error': 'Some contact IDs are invalid'}), 400
        
        # Get active verification webhook
        webhook = WebhookConfig.query.filter_by(
            webhook_type='verification',
            is_active=True
        ).first()
        
        if not webhook:
            return jsonify({'error': 'No active verification webhook configured'}), 400
        
        # Create verification job
        job_id = str(uuid.uuid4())
        verification_job = VerificationJob(
            job_id=job_id,
            contact_ids=json.dumps(contact_ids),
            webhook_config_id=webhook.webhook_id,
            status='pending'
        )
        
        db.session.add(verification_job)
        
        # Update contact statuses to indicate verification is in progress
        for contact in contacts:
            contact.email_verification_status = 'not_verified'
            contact.updated_timestamp = datetime.utcnow()
        
        db.session.commit()
        
        # Prepare data for Make.com webhook
        webhook_data = {
            'job_id': job_id,
            'webhook_type': 'verification',
            'contacts': []
        }
        
        # Parse input fields to determine what data to send
        input_fields = {}
        if webhook.input_fields:
            try:
                input_fields = json.loads(webhook.input_fields)
            except json.JSONDecodeError:
                pass
        
        # Build contact data based on input field configuration
        for contact in contacts:
            contact_data = {
                'contact_id': contact.contact_id,
                'email_address': contact.email_address,
                'first_name': contact.first_name,
                'last_name': contact.last_name
            }
            
            # Add additional fields if specified in input configuration
            if 'company_name' in input_fields:
                contact_data['company_name'] = contact.company_name
            if 'phone_number' in input_fields:
                contact_data['phone_number'] = contact.phone_number
            
            webhook_data['contacts'].append(contact_data)
        
        # Prepare headers for the webhook
        import logging
        logging.basicConfig(level=logging.INFO)
        headers = {'Content-Type': 'application/json'}

        logging.info(f"Processing headers for webhook {webhook.webhook_id}. Raw headers from DB: '{webhook.headers}'")
        if webhook.headers and webhook.headers.strip():
            try:
                custom_headers = json.loads(webhook.headers)
                headers.update(custom_headers)
                logging.info(f"Successfully loaded and updated headers for webhook {webhook.webhook_id}.")
            except json.JSONDecodeError:
                logging.error(f"HEADER PARSE FAILED for webhook {webhook.webhook_id}. Invalid JSON received: {webhook.headers}")
        else:
            logging.warning(f"No custom headers found or headers are empty for webhook {webhook.webhook_id}.")

        # Send webhook to Make.com (async in production)
        try:
            logging.info(f"Sending verification webhook for job {job_id} to {webhook.url}")
            logging.info(f"Final headers being sent: {json.dumps(headers)}")
            # logging.info(f"Webhook body: {json.dumps(webhook_data)}")

            response = requests.post(
                webhook.url,
                json=webhook_data,
                timeout=30,
                headers=headers
            )

            logging.info(f"Webhook response status code: {response.status_code}")
            # logging.info(f"Webhook response body: {response.text}")
            
            if response.status_code == 200:
                verification_job.status = 'processing'
            else:
                verification_job.status = 'failed'
                verification_job.error_message = f'Webhook failed with status {response.status_code}: {response.text}'
            
        except requests.RequestException as e:
            logging.error(f"Webhook request failed: {str(e)}")
            verification_job.status = 'failed'
            verification_job.error_message = str(e)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'contact_count': len(contact_ids),
            'webhook_url': webhook.url,
            'status': verification_job.status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@verification_bp.route('/jobs', methods=['GET'])
def get_verification_jobs():
    """Get verification job history"""
    try:
        jobs = VerificationJob.query.order_by(VerificationJob.created_timestamp.desc()).all()
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@verification_bp.route('/jobs/<job_id>', methods=['GET'])
def get_verification_job(job_id):
    """Get specific verification job details"""
    try:
        job = VerificationJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Verification job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

