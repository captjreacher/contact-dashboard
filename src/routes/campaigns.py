from flask import Blueprint, request, jsonify
import requests
import json
import uuid
from datetime import datetime
from src.models.models import db
from src.models.models import Contact
from src.models.models import Campaign, CampaignResult, CampaignJob, SampleRequest, AuditLog
from src.models.webhook_config import WebhookConfig, VerificationJob, CampaignExecution

campaigns_bp = Blueprint('campaigns', __name__)

@campaigns_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaigns"""
    try:
        campaigns = Campaign.query.order_by(Campaign.created_timestamp.desc()).all()
        
        # Add contact count for each campaign
        campaign_list = []
        for campaign in campaigns:
            campaign_dict = campaign.to_dict()
            # Count contacts associated with this campaign
            contact_count = CampaignResult.query.filter_by(campaign_id=campaign.campaign_id).count()
            campaign_dict['contact_count'] = contact_count
            campaign_list.append(campaign_dict)
        
        return jsonify({
            'success': True,
            'campaigns': campaign_list
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@campaigns_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Campaign name is required'}), 400
        
        campaign = Campaign(
            name=data['name'],
            description=data.get('description', ''),
            status='active',
            created_by='system'  # TODO: Get from session
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/run', methods=['POST'])
def run_campaign(campaign_id):
    """Run a campaign with selected contacts"""
    try:
        data = request.get_json()
        contact_ids = data.get('contact_ids', [])
        job_id = data.get('job_id')
        
        if not contact_ids:
            return jsonify({'error': 'No contacts selected for campaign'}), 400
        
        if not job_id:
            return jsonify({'error': 'Campaign job is required'}), 400
        
        # Validate campaign exists
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Validate campaign job exists
        campaign_job = CampaignJob.query.get(job_id)
        if not campaign_job or not campaign_job.is_active:
            return jsonify({'error': 'Campaign job not found or inactive'}), 404
        
        # Validate that all contact IDs exist and are verified
        contacts = Contact.query.filter(
            Contact.contact_id.in_(contact_ids),
            Contact.email_verification_status == 'valid'
        ).all()
        
        if len(contacts) != len(contact_ids):
            return jsonify({'error': 'Some contacts are invalid or not verified'}), 400
        
        # Create campaign execution record
        execution_id = str(uuid.uuid4())
        campaign_execution = CampaignExecution(
            execution_id=execution_id,
            campaign_id=campaign_id,
            job_id=job_id,
            contact_ids=json.dumps(contact_ids),
            status='pending'
        )
        
        db.session.add(campaign_execution)
        
        # Prepare data for Make.com webhook
        webhook_data = {
            'execution_id': execution_id,
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'job_id': job_id,
            'contacts': []
        }
        
        # Parse input fields to determine what data to send
        input_fields = {}
        if campaign_job.input_fields:
            try:
                input_fields = json.loads(campaign_job.input_fields)
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
            if 'job_title' in input_fields:
                contact_data['job_title'] = contact.job_title
            
            webhook_data['contacts'].append(contact_data)
        
        # Prepare headers for the webhook
        headers = {'Content-Type': 'application/json'}
        if campaign_job.headers:
            try:
                custom_headers = json.loads(campaign_job.headers)
                headers.update(custom_headers)
            except json.JSONDecodeError:
                # Log the error or handle it as needed
                pass

        # Send webhook to Make.com
        try:
            import logging
            logging.basicConfig(level=logging.INFO)
            logging.info(f"Sending campaign webhook for execution {execution_id} to {campaign_job.webhook_url}")
            logging.info(f"Webhook headers: {json.dumps(headers)}")
            # logging.info(f"Webhook body: {json.dumps(webhook_data)}")

            response = requests.post(
                campaign_job.webhook_url,
                json=webhook_data,
                timeout=30,
                headers=headers
            )
            
            logging.info(f"Webhook response status code: {response.status_code}")
            # logging.info(f"Webhook response body: {response.text}")

            if response.status_code == 200:
                campaign_execution.status = 'processing'
                campaign.status = 'active'
            else:
                campaign_execution.status = 'failed'
                campaign_execution.error_message = f'Webhook failed with status {response.status_code}: {response.text}'
            
        except requests.RequestException as e:
            logging.error(f"Webhook request failed: {str(e)}")
            campaign_execution.status = 'failed'
            campaign_execution.error_message = str(e)
        
        db.session.commit()
        
        # Create audit log
        audit_log = AuditLog(
            action='campaign_started',
            details=json.dumps({
                'campaign_id': campaign_id,
                'execution_id': execution_id,
                'contact_count': len(contact_ids),
                'job_id': job_id
            }),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'job_id': execution_id,  # For compatibility with frontend
            'contact_count': len(contact_ids),
            'webhook_url': campaign_job.webhook_url,
            'status': campaign_execution.status
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@campaigns_bp.route('/campaigns/jobs', methods=['GET'])
def get_campaign_jobs():
    """Get available Make.com campaign jobs"""
    try:
        jobs = WebhookCampaignJob.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

