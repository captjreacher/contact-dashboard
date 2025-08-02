from flask import Blueprint, request, jsonify
import uuid
import json
import requests
from datetime import datetime
from src.models.models import db, Contact, VerificationJob
from src.models import WebhookConfig

verification_bp = Blueprint('verification', __name__)

@verification_bp.route('/jobs/run', methods=['POST'])
def run_verification_job():
    """Triggers the verification process for a given job."""
    try:
        data = request.get_json()
        job_id = data.get('job_id')

        if not job_id:
            return jsonify({'error': 'Job ID is required'}), 400

        # Get the verification job
        verification_job = VerificationJob.query.get(job_id)
        if not verification_job:
            return jsonify({'error': 'Verification job not found'}), 404

        if verification_job.status != 'pending':
            return jsonify({'error': f'Job is not in a pending state. Current status: {verification_job.status}'}), 400

        # Get contact IDs from the job
        contact_ids = json.loads(verification_job.contact_ids)
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()

        # Get active verification webhook
        webhook = WebhookConfig.query.filter_by(
            webhook_type='verification',
            is_active=True
        ).first()

        if not webhook:
            return jsonify({'error': 'No active verification webhook configured'}), 400
        
        # Prepare data for the webhook
        webhook_data = {
            'job_id': job_id,
            'contacts': [
                {'contact_id': c.contact_id, 'email': c.email_address} for c in contacts
            ]
        }
        
        headers = {'Content-Type': 'application/json'}
        if webhook.header_name and webhook.header_value:
            headers[webhook.header_name] = webhook.header_value

        # Send webhook to Make.com
        try:
            response = requests.post(webhook.url, json=webhook_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                verification_job.status = 'processing'
                verification_job.webhook_config_id = webhook.webhook_id
            else:
                verification_job.status = 'failed'
                verification_job.error_message = f'Webhook failed with status {response.status_code}: {response.text}'

        except requests.RequestException as e:
            verification_job.status = 'failed'
            verification_job.error_message = str(e)

        db.session.commit()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': verification_job.status,
            'error_message': verification_job.error_message
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@verification_bp.route('/jobs', methods=['GET', 'POST'])
def handle_verification_jobs():
    """Handle getting and creating verification jobs."""
    if request.method == 'POST':
        return create_verification_job()
    return get_verification_jobs()

def create_verification_job():
    """Create a new verification job."""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])

        if not contact_ids:
            return jsonify({'error': 'No contact IDs provided'}), 400

        # Create a new verification job
        job_id = str(uuid.uuid4())
        new_job = VerificationJob(
            job_id=job_id,
            contact_ids=json.dumps(contact_ids),
            status='pending',
        )

        db.session.add(new_job)
        db.session.commit()

        return jsonify({
            'success': True,
            'job': new_job.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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

