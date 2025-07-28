from flask import Blueprint, request, jsonify
import uuid
import json
from datetime import datetime
from src.models.models import db
from src.models.webhook_config import WebhookConfig, CampaignJob

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/webhooks', methods=['GET'])
def get_webhooks():
    """Get all webhook configurations"""
    try:
        webhooks = WebhookConfig.query.all()
        return jsonify({
            'success': True,
            'webhooks': [webhook.to_dict() for webhook in webhooks]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/webhooks', methods=['POST'])
def create_webhook():
    """Create a new webhook configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Webhook name is required'}), 400
        if not data.get('url'):
            return jsonify({'error': 'Webhook URL is required'}), 400
        if not data.get('webhook_type'):
            return jsonify({'error': 'Webhook type is required'}), 400
        
        # Validate webhook type
        if data['webhook_type'] not in ['verification', 'campaign']:
            return jsonify({'error': 'Invalid webhook type'}), 400
        
        # Validate JSON fields if provided
        if data.get('input_fields'):
            try:
                json.loads(data['input_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for input fields'}), 400
        
        if data.get('output_fields'):
            try:
                json.loads(data['output_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for output fields'}), 400
        
        webhook = WebhookConfig(
            webhook_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            webhook_type=data['webhook_type'],
            url=data['url'],
            input_fields=data.get('input_fields', ''),
            output_fields=data.get('output_fields', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(webhook)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'webhook': webhook.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/webhooks/<webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    """Update an existing webhook configuration"""
    try:
        webhook = WebhookConfig.query.get(webhook_id)
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        data = request.get_json()
        
        # Validate JSON fields if provided
        if data.get('input_fields'):
            try:
                json.loads(data['input_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for input fields'}), 400
        
        if data.get('output_fields'):
            try:
                json.loads(data['output_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for output fields'}), 400
        
        # Update fields
        if 'name' in data:
            webhook.name = data['name']
        if 'description' in data:
            webhook.description = data['description']
        if 'webhook_type' in data:
            if data['webhook_type'] not in ['verification', 'campaign']:
                return jsonify({'error': 'Invalid webhook type'}), 400
            webhook.webhook_type = data['webhook_type']
        if 'url' in data:
            webhook.url = data['url']
        if 'input_fields' in data:
            webhook.input_fields = data['input_fields']
        if 'output_fields' in data:
            webhook.output_fields = data['output_fields']
        if 'is_active' in data:
            webhook.is_active = data['is_active']
        
        webhook.updated_timestamp = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'webhook': webhook.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/webhooks/<webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    """Delete a webhook configuration"""
    try:
        webhook = WebhookConfig.query.get(webhook_id)
        if not webhook:
            return jsonify({'error': 'Webhook not found'}), 404
        
        db.session.delete(webhook)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/campaign-jobs', methods=['GET'])
def get_campaign_jobs():
    """Get all campaign job configurations"""
    try:
        jobs = CampaignJob.query.all()
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/campaign-jobs', methods=['POST'])
def create_campaign_job():
    """Create a new campaign job configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Job name is required'}), 400
        if not data.get('webhook_url'):
            return jsonify({'error': 'Webhook URL is required'}), 400
        
        # Validate JSON fields if provided
        if data.get('input_fields'):
            try:
                json.loads(data['input_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for input fields'}), 400
        
        if data.get('output_fields'):
            try:
                json.loads(data['output_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for output fields'}), 400
        
        job = CampaignJob(
            job_id=str(uuid.uuid4()),
            name=data['name'],
            description=data.get('description', ''),
            webhook_url=data['webhook_url'],
            input_fields=data.get('input_fields', ''),
            output_fields=data.get('output_fields', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/campaign-jobs/<job_id>', methods=['PUT'])
def update_campaign_job(job_id):
    """Update an existing campaign job configuration"""
    try:
        job = CampaignJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Campaign job not found'}), 404
        
        data = request.get_json()
        
        # Validate JSON fields if provided
        if data.get('input_fields'):
            try:
                json.loads(data['input_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for input fields'}), 400
        
        if data.get('output_fields'):
            try:
                json.loads(data['output_fields'])
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format for output fields'}), 400
        
        # Update fields
        if 'name' in data:
            job.name = data['name']
        if 'description' in data:
            job.description = data['description']
        if 'webhook_url' in data:
            job.webhook_url = data['webhook_url']
        if 'input_fields' in data:
            job.input_fields = data['input_fields']
        if 'output_fields' in data:
            job.output_fields = data['output_fields']
        if 'is_active' in data:
            job.is_active = data['is_active']
        
        job.updated_timestamp = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/campaign-jobs/<job_id>', methods=['DELETE'])
def delete_campaign_job(job_id):
    """Delete a campaign job configuration"""
    try:
        job = CampaignJob.query.get(job_id)
        if not job:
            return jsonify({'error': 'Campaign job not found'}), 404
        
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

