import os
from flask import Blueprint, request, jsonify
import json
import hmac
import hashlib
from datetime import datetime
from src.models.models import (
    db, Contact, Campaign, CampaignResult, SampleRequest, AuditLog, 
    VerificationJob, CampaignExecution, Webhook
)

webhooks_bp = Blueprint('webhooks', __name__)

def verify_webhook_signature(payload, signature, secret_key='webhook_secret'):
    """Verify webhook signature from Make.com"""
    if not signature:
        return False
    
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@webhooks_bp.route("/verification-results", methods=["POST"])
def receive_verification_results():
    """Receive email verification results from Make.com"""
    try:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ.get("WEBHOOK_API_KEY"):
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing API Key"}), 401

        payload = request.get_data()
        signature = request.headers.get("X-Make-Signature")
        
        # Signature verification (commented out for dev)
        # if not verify_webhook_signature(payload, signature):
        #     return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        job_id = data.get('job_id')
        results = data.get('results', [])
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Missing job_id'}), 400
        
        if not results:
            return jsonify({'success': False, 'error': 'No verification results provided'}), 400
        
        verification_job = VerificationJob.query.get(job_id)
        if not verification_job:
            return jsonify({'success': False, 'error': 'Verification job not found'}), 404
        
        updated_contacts = 0
        for result in results:
            contact_id = result.get('contact_id')
            status = result.get('status', 'unknown')
            details = result.get('details', {})
            
            if not contact_id:
                continue
            
            contact = Contact.query.get(contact_id)
            if contact:
                contact.email_verification_status = status
                contact.email_verification_date = datetime.utcnow()
                contact.email_verification_details = json.dumps(details)
                contact.updated_timestamp = datetime.utcnow()
                updated_contacts += 1
        
        verification_job.status = 'completed'
        verification_job.completed_timestamp = datetime.utcnow()
        
        audit_log = AuditLog(
            action='verification_results_received',
            details=json.dumps({
                'job_id': job_id,
                'updated_contacts': updated_contacts,
                'total_results': len(results)
            }),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'updated_contacts': updated_contacts,
            'total_results': len(results)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@webhooks_bp.route("/campaign-results", methods=["POST"])
def receive_campaign_results():
    """Receive campaign results from Make.com"""
    try:
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ.get("WEBHOOK_API_KEY"):
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing API Key"}), 401

        payload = request.get_data()
        signature = request.headers.get("X-Make-Signature")
        
        # Signature verification (commented out for dev)
        # if not verify_webhook_signature(payload, signature):
        #     return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        execution_id = data.get('execution_id')
        results = data.get('results', [])
        
        if 'contact_id' in data and 'campaign_id' in data:
            results = [{
                'contact_id': data['contact_id'],
                'campaign_id': data['campaign_id'],
                'status': data.get('status', 'completed'),
                'error_code': data.get('error_code'),
                'result_date': data.get('result_date', datetime.utcnow().isoformat())
            }]
        
        if not results:
            return jsonify({'success': False, 'error': 'No campaign results provided'}), 400
        
        campaign_execution = None
        if execution_id:
            campaign_execution = CampaignExecution.query.get(execution_id)
        
        updated_contacts = 0
        for result in results:
            contact_id = result.get('contact_id')
            campaign_id = result.get('campaign_id')
            status = result.get('status', 'completed')
            error_code = result.get('error_code')
            result_date = result.get('result_date')
            
            if not contact_id or not campaign_id:
                continue
            
            contact = Contact.query.get(contact_id)
            campaign = Campaign.query.get(campaign_id)
            
            if not contact or not campaign:
                continue
            
            if status == 'completed' and not error_code:
                if result_date:
                    try:
                        date_obj = datetime.fromisoformat(result_date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%d.%m.%Y')
                    except:
                        formatted_date = datetime.utcnow().strftime('%d.%m.%Y')
                else:
                    formatted_date = datetime.utcnow().strftime('%d.%m.%Y')
                
                contact.campaign_status = f"Campaign {campaign.name}: {formatted_date}"
            elif error_code:
                contact.campaign_status = f"Campaign {campaign.name}: No result-{error_code}"
            else:
                contact.campaign_status = f"Campaign {campaign.name}: No result"
            
            contact.updated_timestamp = datetime.utcnow()
            updated_contacts += 1
            
            campaign_result = CampaignResult.query.filter_by(
                campaign_id=campaign_id,
                contact_id=contact_id
            ).first()
            
            if not campaign_result:
                campaign_result = CampaignResult(
                    campaign_id=campaign_id,
                    contact_id=contact_id,
                    processing_status=status
                )
                db.session.add(campaign_result)
            else:
                campaign_result.processing_status = status
            
            if result_date:
                try:
                    campaign_result.delivery_timestamp = datetime.fromisoformat(
                        result_date.replace('Z', '+00:00')
                    )
                except ValueError:
                    pass
        
        if campaign_execution:
            campaign_execution.status = 'completed'
            campaign_execution.completed_timestamp = datetime.utcnow()
        
        audit_log = AuditLog(
            action='campaign_results_received',
            details=json.dumps({
                'execution_id': execution_id,
                'updated_contacts': updated_contacts,
                'total_results': len(results)
            }),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'updated_contacts': updated_contacts,
            'total_results': len(results)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- New Webhook Management API ---

@webhooks_bp.route('/api/settings/webhooks', methods=['GET'])
def get_webhooks():
    webhooks = Webhook.query.all()
    result = []
    for w in webhooks:
        result.append({
            'id': w.id,
            'url': w.url,
            'events': json.loads(w.events) if w.events else [],
            'headers': w.headers or '{}'
        })
    return jsonify(success=True, webhooks=result)

@webhooks_bp.route('/api/settings/webhooks', methods=['POST'])
def create_webhook():
    data = request.json
    url = data.get('url')
    events = data.get('events', [])
    headers = data.get('headers', '{}')

    if not url:
        return jsonify(success=False, error='URL is required'), 400
    try:
        json.loads(headers)
    except Exception:
        return jsonify(success=False, error='Invalid JSON for headers'), 400

    webhook = Webhook(
        url=url,
        events=json.dumps(events),
        headers=headers
    )
    db.session.add(webhook)
    db.session.commit()

    return jsonify(success=True, webhook={
        'id': webhook.id,
        'url': webhook.url,
        'events': events,
        'headers': headers
    }), 201

@webhooks_bp.route('/api/settings/webhooks/<int:webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    webhook = Webhook.query.get(webhook_id)
    if not webhook:
        return jsonify(success=False, error='Webhook not found'), 404

    data = request.json
    url = data.get('url')
    events = data.get('events')
    headers = data.get('headers')

    if url:
        webhook.url = url
    if events is not None:
        webhook.events = json.dumps(events)
    if headers is not None:
        try:
            json.loads(headers)
        except Exception:
            return jsonify(success=False, error='Invalid JSON for headers'), 400
        webhook.headers = headers

    db.session.commit()

    return jsonify(success=True, webhook={
        'id': webhook.id,
        'url': webhook.url,
        'events': json.loads(webhook.events) if webhook.events else [],
        'headers': webhook.headers or '{}'
    })

