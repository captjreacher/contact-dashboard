from flask import Blueprint, request, jsonify
import json
import hmac
import hashlib
from datetime import datetime
from src.models.models import db
from src.models.models import Contact
from src.models.models import Campaign, CampaignResult
from src.models.models import SampleRequest, AuditLog

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

@webhooks_bp.route('/webhooks/campaign-results', methods=['POST'])
def receive_campaign_results():
    """Receive campaign results from Make.com"""
    try:
        # Get raw payload for signature verification
        payload = request.get_data()
        signature = request.headers.get('X-Make-Signature')
        
        # Verify signature (commented out for development)
        # if not verify_webhook_signature(payload, signature):
        #     return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        # Parse JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['campaign_id', 'contact_id', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        campaign_id = data['campaign_id']
        contact_id = data['contact_id']
        status = data['status']
        
        # Verify campaign and contact exist
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Find existing campaign result or create new one
        result = CampaignResult.query.filter_by(
            campaign_id=campaign_id,
            contact_id=contact_id
        ).first()
        
        if not result:
            # Create new result if it doesn't exist
            result = CampaignResult(
                campaign_id=campaign_id,
                contact_id=contact_id,
                processing_status='pending'
            )
            db.session.add(result)
            db.session.flush()  # Get the result ID
        
        # Update result with Make.com response
        result.processing_status = status
        
        if 'delivery_timestamp' in data:
            try:
                result.delivery_timestamp = datetime.fromisoformat(
                    data['delivery_timestamp'].replace('Z', '+00:00')
                )
            except ValueError:
                pass
        
        if 'scenario_execution_id' in data:
            result.set_make_response({'scenario_execution_id': data['scenario_execution_id']})
        
        if 'response_data' in data:
            result.set_response_data(data['response_data'])
        
        # Handle sample request
        sample_requested = data.get('sample_requested', False)
        sample_request_id = None
        
        if sample_requested:
            result.sample_requested = True
            
            # Create sample request if it doesn't exist
            existing_sample = SampleRequest.query.filter_by(
                contact_id=contact_id,
                campaign_id=campaign_id,
                result_id=result.result_id
            ).first()
            
            if not existing_sample:
                sample_details = data.get('sample_details', {})
                
                # Prepare shipping address
                shipping_address = {}
                if 'shipping_address' in sample_details:
                    shipping_address = sample_details['shipping_address']
                elif contact:
                    # Use contact address as fallback
                    shipping_address = {
                        'line1': contact.address_line1,
                        'line2': contact.address_line2,
                        'city': contact.city,
                        'state': contact.state_province,
                        'postal_code': contact.postal_code,
                        'country': contact.country
                    }
                
                sample_request = SampleRequest(
                    contact_id=contact_id,
                    campaign_id=campaign_id,
                    result_id=result.result_id,
                    sample_type=sample_details.get('sample_type', 'Standard Sample'),
                    quantity_requested=sample_details.get('quantity', 1),
                    fulfillment_status='pending'
                )
                
                if shipping_address:
                    sample_request.set_shipping_address(shipping_address)
                
                db.session.add(sample_request)
                db.session.flush()
                sample_request_id = sample_request.request_id
        
        # Update campaign statistics
        if status == 'delivered':
            # Check if this was previously failed and now successful
            if result.processing_status in ['failed', 'bounced']:
                campaign.failed_contacts = max(0, campaign.failed_contacts - 1)
            campaign.successful_contacts += 1
        elif status in ['failed', 'bounced']:
            # Check if this was previously successful and now failed
            if result.processing_status == 'delivered':
                campaign.successful_contacts = max(0, campaign.successful_contacts - 1)
            campaign.failed_contacts += 1
        
        db.session.commit()
        
        # Log the webhook receipt
        AuditLog.log_action(
            user_id='webhook',
            action_type='webhook_received',
            table_name='campaign_results',
            record_id=result.result_id,
            new_values=data,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        
        response_data = {
            'success': True,
            'result_id': result.result_id,
            'message': 'Campaign result processed successfully'
        }
        
        if sample_request_id:
            response_data['sample_request_id'] = sample_request_id
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        
        # Log the error
        try:
            AuditLog.log_action(
                user_id='webhook',
                action_type='webhook_error',
                table_name='campaign_results',
                new_values={'error': str(e), 'data': request.get_json()},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.commit()
        except:
            pass
        
        return jsonify({'success': False, 'error': str(e)}), 500

@webhooks_bp.route('/webhooks/test', methods=['POST'])
def test_webhook():
    """Test webhook endpoint for development"""
    try:
        data = request.get_json()
        
        return jsonify({
            'success': True,
            'message': 'Webhook test successful',
            'received_data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@webhooks_bp.route('/webhooks/status', methods=['GET'])
def webhook_status():
    """Get webhook service status"""
    try:
        # Get recent webhook activity
        recent_webhooks = AuditLog.query.filter_by(
            action_type='webhook_received'
        ).order_by(AuditLog.timestamp.desc()).limit(10).all()
        
        recent_errors = AuditLog.query.filter_by(
            action_type='webhook_error'
        ).order_by(AuditLog.timestamp.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'status': 'active',
            'recent_webhooks': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'table_name': log.table_name,
                    'record_id': log.record_id
                }
                for log in recent_webhooks
            ],
            'recent_errors': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'error': log.get_new_values().get('error', 'Unknown error')
                }
                for log in recent_errors
            ]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@webhooks_bp.route('/webhooks/simulate-campaign-result', methods=['POST'])
def simulate_campaign_result():
    """Simulate a campaign result webhook for testing"""
    try:
        data = request.get_json()
        
        # Default test data
        test_data = {
            'campaign_id': data.get('campaign_id', 1),
            'contact_id': data.get('contact_id', 1),
            'scenario_execution_id': f"test_exec_{datetime.utcnow().timestamp()}",
            'status': data.get('status', 'delivered'),
            'delivery_timestamp': datetime.utcnow().isoformat(),
            'sample_requested': data.get('sample_requested', True),
            'sample_details': {
                'sample_type': data.get('sample_type', 'Test Sample Kit'),
                'quantity': data.get('quantity', 1),
                'shipping_address': data.get('shipping_address', {
                    'line1': '123 Test St',
                    'line2': 'Suite 100',
                    'city': 'Test City',
                    'state': 'TS',
                    'postal_code': '12345',
                    'country': 'USA'
                })
            },
            'response_data': {
                'email_opened': True,
                'links_clicked': ['product_info', 'sample_request'],
                'engagement_score': 85
            }
        }
        
        # Call the actual webhook handler
        from flask import Flask
        with Flask(__name__).test_request_context(
            '/webhooks/campaign-results',
            method='POST',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        ):
            result = receive_campaign_results()
            return result
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

