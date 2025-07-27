from flask import Blueprint, request, jsonify
import requests
import json
import time
from datetime import datetime
from src.models.models import db
from src.models.models import Contact
from src.models.models import Campaign, CampaignResult, CampaignJob
from src.models.models import SampleRequest, AuditLog

campaigns_bp = Blueprint('campaigns', __name__)

@campaigns_bp.route('/campaigns/jobs', methods=['GET'])
def get_campaign_jobs():
    """Get available Make.com campaign jobs"""
    try:
        jobs = CampaignJob.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/jobs', methods=['POST'])
def create_campaign_job():
    """Create a new campaign job"""
    try:
        data = request.get_json()
        
        job = CampaignJob(
            job_name=data['job_name'],
            job_description=data.get('job_description'),
            webhook_url=data['webhook_url'],
            make_scenario_id=data.get('make_scenario_id'),
            created_by='system'  # TODO: Get from session
        )
        
        if 'parameters' in data:
            job.set_job_parameters(data['parameters'])
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create new campaign"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('campaign_name'):
            return jsonify({'success': False, 'error': 'Campaign name is required'}), 400
        
        if not data.get('job_name'):
            return jsonify({'success': False, 'error': 'Job name is required'}), 400
        
        if not data.get('selected_contacts'):
            return jsonify({'success': False, 'error': 'No contacts selected'}), 400
        
        # Get job details
        job = CampaignJob.query.filter_by(job_name=data['job_name'], is_active=True).first()
        if not job:
            return jsonify({'success': False, 'error': 'Invalid job name'}), 400
        
        # Validate selected contacts exist
        contact_ids = data['selected_contacts']
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()
        
        if len(contacts) != len(contact_ids):
            return jsonify({'success': False, 'error': 'Some selected contacts not found'}), 400
        
        # Create campaign
        campaign = Campaign(
            campaign_name=data['campaign_name'],
            job_name=data['job_name'],
            job_webhook_url=job.webhook_url,
            campaign_description=data.get('description'),
            total_contacts=len(contact_ids),
            created_by='system',  # TODO: Get from session
            make_scenario_id=job.make_scenario_id
        )
        
        campaign.set_selected_contact_ids(contact_ids)
        
        if 'campaign_settings' in data:
            campaign.set_campaign_settings(data['campaign_settings'])
        
        db.session.add(campaign)
        db.session.commit()
        
        # Log campaign creation
        AuditLog.log_action(
            user_id='system',
            action_type='create',
            table_name='campaigns',
            record_id=campaign.campaign_id,
            new_values=campaign.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

import threading
from flask import current_app

def run_campaign_in_background(app, campaign_id):
    with app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return

        # Get selected contacts
        contact_ids = campaign.get_selected_contact_ids()
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()

        # Process contacts one by one
        for contact in contacts:
            try:
                # Create campaign result record
                result = CampaignResult(
                    campaign_id=campaign_id,
                    contact_id=contact.contact_id,
                    processing_status='pending'
                )
                db.session.add(result)
                db.session.flush()  # Get the result ID

                # Prepare payload for Make.com
                payload = {
                    'campaign_id': campaign_id,
                    'contact_id': contact.contact_id,
                    'result_id': result.result_id,
                    'contact_data': {
                        'first_name': contact.first_name,
                        'last_name': contact.last_name,
                        'email_address': contact.email_address,
                        'phone_number': contact.phone_number,
                        'company_name': contact.company_name,
                        'job_title': contact.job_title,
                        'address': {
                            'line1': contact.address_line1,
                            'line2': contact.address_line2,
                            'city': contact.city,
                            'state': contact.state_province,
                            'postal_code': contact.postal_code,
                            'country': contact.country
                        }
                    },
                    'campaign_settings': campaign.get_campaign_settings()
                }

                # Send to Make.com webhook
                try:
                    response = requests.post(
                        campaign.job_webhook_url,
                        json=payload,
                        timeout=30,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code == 200:
                        result.processing_status = 'sent'
                        result.set_make_response(response.json() if response.content else {})
                        campaign.successful_contacts += 1
                    else:
                        result.processing_status = 'failed'
                        result.error_message = f"HTTP {response.status_code}: {response.text}"
                        campaign.failed_contacts += 1

                except requests.exceptions.RequestException as e:
                    result.processing_status = 'failed'
                    result.error_message = str(e)
                    campaign.failed_contacts += 1

                result.processed_timestamp = datetime.utcnow()
                campaign.processed_contacts += 1

                db.session.commit()

                # Add delay between requests to avoid overwhelming Make.com
                time.sleep(1)

            except Exception as e:
                # Log error but continue with other contacts
                print(f"Error processing contact {contact.contact_id}: {str(e)}")
                campaign.failed_contacts += 1
                campaign.processed_contacts += 1
                db.session.commit()

        # Update campaign completion
        campaign.campaign_status = 'completed'
        campaign.execution_end_time = datetime.utcnow()
        db.session.commit()
        db.session.remove()


@campaigns_bp.route('/campaigns/<int:campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Start campaign execution"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404

        if campaign.campaign_status != 'draft':
            return jsonify({'success': False, 'error': 'Campaign is not in draft status'}), 400

        # Update campaign status
        campaign.campaign_status = 'running'
        campaign.execution_start_time = datetime.utcnow()
        db.session.commit()

        # Run campaign in background thread
        app = current_app._get_current_object()
        thread = threading.Thread(target=run_campaign_in_background, args=(app, campaign_id))
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'status': 'running',
            'message': 'Campaign started in the background.'
        })

    except Exception as e:
        # Update campaign status to failed
        if 'campaign' in locals():
            campaign.campaign_status = 'failed'
            campaign.execution_end_time = datetime.utcnow()
            db.session.commit()

        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/status', methods=['GET'])
def get_campaign_status(campaign_id):
    """Get campaign execution status"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Get current contact being processed (if running)
        current_contact = None
        if campaign.campaign_status == 'running':
            # Find the last processed contact
            last_result = CampaignResult.query.filter_by(
                campaign_id=campaign_id
            ).order_by(CampaignResult.processed_timestamp.desc()).first()
            
            if last_result:
                contact = Contact.query.get(last_result.contact_id)
                if contact:
                    current_contact = {
                        'contact_id': contact.contact_id,
                        'email': contact.email_address,
                        'processing_status': last_result.processing_status
                    }
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'status': campaign.campaign_status,
            'progress': {
                'total_contacts': campaign.total_contacts,
                'processed_contacts': campaign.processed_contacts,
                'successful_contacts': campaign.successful_contacts,
                'failed_contacts': campaign.failed_contacts
            },
            'execution_start_time': campaign.execution_start_time.isoformat() if campaign.execution_start_time else None,
            'execution_end_time': campaign.execution_end_time.isoformat() if campaign.execution_end_time else None,
            'current_contact': current_contact
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns', methods=['GET'])
def get_campaigns():
    """List all campaigns with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        job_name = request.args.get('job_name')
        created_by = request.args.get('created_by')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = Campaign.query
        
        if status:
            query = query.filter_by(campaign_status=status)
        
        if job_name:
            query = query.filter_by(job_name=job_name)
        
        if created_by:
            query = query.filter_by(created_by=created_by)
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(Campaign.created_timestamp >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(Campaign.created_timestamp <= date_to_obj)
            except ValueError:
                pass
        
        # Order by creation date (newest first)
        query = query.order_by(Campaign.created_timestamp.desc())
        
        # Paginate
        campaigns = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'total_campaigns': campaigns.total,
            'page': page,
            'per_page': per_page,
            'total_pages': campaigns.pages,
            'campaigns': [campaign.to_summary_dict() for campaign in campaigns.items]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get detailed campaign information"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        return jsonify({
            'success': True,
            'campaign': campaign.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/results', methods=['GET'])
def get_campaign_results(campaign_id):
    """Get campaign results"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')
        
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Build query
        query = db.session.query(CampaignResult, Contact).join(
            Contact, CampaignResult.contact_id == Contact.contact_id
        ).filter(CampaignResult.campaign_id == campaign_id)
        
        if status:
            query = query.filter(CampaignResult.processing_status == status)
        
        # Paginate
        results = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        result_data = []
        for result, contact in results.items:
            result_dict = result.to_dict()
            result_dict['contact'] = contact.to_summary_dict()
            result_data.append(result_dict)
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'total_results': results.total,
            'page': page,
            'per_page': per_page,
            'total_pages': results.pages,
            'results': result_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/contacts', methods=['GET'])
def get_campaign_contacts(campaign_id):
    """Get contacts associated with campaign"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        contact_ids = campaign.get_selected_contact_ids()
        contacts = Contact.query.filter(Contact.contact_id.in_(contact_ids)).all()
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'total_contacts': len(contacts),
            'contacts': [contact.to_summary_dict() for contact in contacts]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_bp.route('/campaigns/<int:campaign_id>/export', methods=['GET'])
def export_campaign_results(campaign_id):
    """Export campaign results to CSV"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Get all campaign results with contact info
        results = db.session.query(CampaignResult, Contact).join(
            Contact, CampaignResult.contact_id == Contact.contact_id
        ).filter(CampaignResult.campaign_id == campaign_id).all()
        
        # Convert to CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Result ID', 'Contact ID', 'First Name', 'Last Name', 'Email Address',
            'Company Name', 'Processing Status', 'Processed Date', 'Delivery Date',
            'Sample Requested', 'Error Message'
        ])
        
        # Write data
        for result, contact in results:
            writer.writerow([
                result.result_id,
                contact.contact_id,
                contact.first_name,
                contact.last_name,
                contact.email_address,
                contact.company_name,
                result.processing_status,
                result.processed_timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.processed_timestamp else '',
                result.delivery_timestamp.strftime('%Y-%m-%d %H:%M:%S') if result.delivery_timestamp else '',
                'Yes' if result.sample_requested else 'No',
                result.error_message or ''
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=campaign_{campaign_id}_results.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

