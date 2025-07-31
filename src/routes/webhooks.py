import os
from flask import Blueprint, request, jsonify
import json
import hmac
import hashlib
from datetime import datetime
from src.models.models import db, Contact, Campaign, CampaignResult, SampleRequest, AuditLog, VerificationJob, CampaignExecution

webhooks_bp = Blueprint('webhooks', __name__)

def verify_webhook_signature(payload, signature, secret_key='webhook_secret'):
    """Verify webhook signature from Make.com"""
    if not signature:
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(signature, expected_signature)

@webhooks_bp.route("/verification-results", methods=["POST"])
def receive_verification_results():
    """Receive email verification results from Make.com"""
    try:
        # API Key authentication
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ.get("WEBHOOK_API_KEY"):
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing API Key"}), 401

        # Get raw payload for signature verification
        payload = request.get_data()
        signature = request.headers.get("X-Make-Signature")
        
        # Verify signature (commented out for development)
        # if not verify_webhook_signature(payload, signature):
        #     return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        # Parse JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        job_id = data.get('job_id')
        results = data.get('results', [])
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Missing job_id'}), 400
        
        if not results:
            return jsonify({'success': False, 'error': 'No verification results provided'}), 400
        
        # Find the verification job
        verification_job = VerificationJob.query.get(job_id)
        if not verification_job:
            return jsonify({'success': False, 'error': 'Verification job not found'}), 404
        
        # Process verification results
        updated_contacts = 0
        for result in results:
            contact_id = result.get('contact_id')
            status = result.get('status', 'unknown')  # valid, invalid, risky, unknown
            details = result.get('details', {})
            
            if not contact_id:
                continue
            
            # Find and update the contact
            contact = Contact.query.get(contact_id)
            if contact:
                contact.email_verification_status = status
                contact.email_verification_date = datetime.utcnow()
                contact.email_verification_details = json.dumps(details)
                contact.updated_timestamp = datetime.utcnow()
                updated_contacts += 1
        
        # Update verification job status
        verification_job.status = 'completed'
        verification_job.completed_timestamp = datetime.utcnow()
        
        # Create audit log
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
        # API Key authentication
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != os.environ.get("WEBHOOK_API_KEY"):
            return jsonify({"success": False, "error": "Unauthorized: Invalid or missing API Key"}), 401

        # Get raw payload for signature verification
        payload = request.get_data()
        signature = request.headers.get("X-Make-Signature")
        
        # Verify signature (commented out for development)
        # if not verify_webhook_signature(payload, signature):
        #     return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        # Parse JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Handle both single contact and batch results
        execution_id = data.get('execution_id')
        results = data.get('results', [])
        
        # If single contact result, convert to list format
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
        
        # Find campaign execution if execution_id provided
        campaign_execution = None
        if execution_id:
            campaign_execution = CampaignExecution.query.get(execution_id)
        
        # Process campaign results
        updated_contacts = 0
        for result in results:
            contact_id = result.get('contact_id')
            campaign_id = result.get('campaign_id')
            status = result.get('status', 'completed')
            error_code = result.get('error_code')
            result_date = result.get('result_date')
            
            if not contact_id or not campaign_id:
                continue
            
            # Find the contact and campaign
            contact = Contact.query.get(contact_id)
            campaign = Campaign.query.get(campaign_id)
            
            if not contact or not campaign:
                continue
            
            # Update contact campaign status
            if status == 'completed' and not error_code:
                # Successful campaign
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
                # Campaign with error
                contact.campaign_status = f"Campaign {campaign.name}: No result-{error_code}"
            else:
                # Failed campaign
                contact.campaign_status = f"Campaign {campaign.name}: No result"
            
            contact.updated_timestamp = datetime.utcnow()
            updated_contacts += 1
            
            # Create or update campaign result record
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
        
        # Update campaign execution status if found
        if campaign_execution:
            campaign_execution.status = 'completed'
            campaign_execution.completed_timestamp = datetime.utcnow()
        
        # Create audit log
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
