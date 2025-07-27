from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.models import db
from src.models.models import Contact
from src.models.models import Campaign, CampaignResult
from src.models.models import SampleRequest, AuditLog

samples_bp = Blueprint('samples', __name__)

@samples_bp.route('/samples', methods=['GET'])
def get_sample_requests():
    """Get sample requests with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')
        campaign_id = request.args.get('campaign_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        fulfilled_by = request.args.get('fulfilled_by')
        
        # Build query with joins
        query = db.session.query(SampleRequest, Contact, Campaign).join(
            Contact, SampleRequest.contact_id == Contact.contact_id
        ).join(
            Campaign, SampleRequest.campaign_id == Campaign.campaign_id
        )
        
        # Apply filters
        if status:
            query = query.filter(SampleRequest.fulfillment_status == status)
        
        if campaign_id:
            query = query.filter(SampleRequest.campaign_id == campaign_id)
        
        if fulfilled_by:
            query = query.filter(SampleRequest.fulfilled_by == fulfilled_by)
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(SampleRequest.request_timestamp >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(SampleRequest.request_timestamp <= date_to_obj)
            except ValueError:
                pass
        
        # Order by request date (newest first)
        query = query.order_by(SampleRequest.request_timestamp.desc())
        
        # Paginate
        results = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        sample_requests = []
        for sample, contact, campaign in results.items:
            sample_dict = sample.to_dict()
            sample_dict['contact'] = {
                'contact_id': contact.contact_id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email_address': contact.email_address,
                'company_name': contact.company_name,
                'phone_number': contact.phone_number
            }
            sample_dict['campaign'] = {
                'campaign_id': campaign.campaign_id,
                'campaign_name': campaign.campaign_name
            }
            sample_requests.append(sample_dict)
        
        return jsonify({
            'success': True,
            'total_requests': results.total,
            'page': page,
            'per_page': per_page,
            'total_pages': results.pages,
            'sample_requests': sample_requests
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/<int:request_id>', methods=['GET'])
def get_sample_request(request_id):
    """Get detailed sample request information"""
    try:
        # Get sample request with related data
        result = db.session.query(SampleRequest, Contact, Campaign).join(
            Contact, SampleRequest.contact_id == Contact.contact_id
        ).join(
            Campaign, SampleRequest.campaign_id == Campaign.campaign_id
        ).filter(SampleRequest.request_id == request_id).first()
        
        if not result:
            return jsonify({'success': False, 'error': 'Sample request not found'}), 404
        
        sample, contact, campaign = result
        
        sample_dict = sample.to_dict()
        sample_dict['contact'] = contact.to_dict()
        sample_dict['campaign'] = campaign.to_dict()
        
        return jsonify({
            'success': True,
            'sample_request': sample_dict
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/<int:request_id>', methods=['PUT'])
def update_sample_request(request_id):
    """Update sample request fulfillment"""
    try:
        sample = SampleRequest.query.get(request_id)
        if not sample:
            return jsonify({'success': False, 'error': 'Sample request not found'}), 404
        
        data = request.get_json()
        
        # Store old values for audit
        old_values = sample.to_dict()
        
        # Update fields
        if 'fulfillment_status' in data:
            sample.fulfillment_status = data['fulfillment_status']
        
        if 'shipped_date' in data:
            if data['shipped_date']:
                sample.shipped_date = datetime.fromisoformat(data['shipped_date'].replace('Z', '+00:00'))
            else:
                sample.shipped_date = None
        
        if 'tracking_number' in data:
            sample.tracking_number = data['tracking_number']
        
        if 'shipping_carrier' in data:
            sample.shipping_carrier = data['shipping_carrier']
        
        if 'quantity_shipped' in data:
            sample.quantity_shipped = data['quantity_shipped']
        
        if 'fulfillment_notes' in data:
            sample.fulfillment_notes = data['fulfillment_notes']
        
        if 'fulfillment_cost' in data:
            sample.fulfillment_cost = data['fulfillment_cost']
        
        if 'fulfilled_by' in data:
            sample.fulfilled_by = data['fulfilled_by']
        
        # If status is being set to shipped, set shipped_date if not provided
        if data.get('fulfillment_status') == 'shipped' and not sample.shipped_date:
            sample.shipped_date = datetime.utcnow()
        
        db.session.commit()
        
        # Log the update
        AuditLog.log_action(
            user_id='system',  # TODO: Get from session
            action_type='update',
            table_name='sample_requests',
            record_id=request_id,
            old_values=old_values,
            new_values=sample.to_dict(),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sample_request': sample.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/bulk-update', methods=['POST'])
def bulk_update_samples():
    """Update multiple sample requests"""
    try:
        data = request.get_json()
        request_ids = data.get('request_ids', [])
        updates = data.get('updates', {})
        
        if not request_ids:
            return jsonify({'success': False, 'error': 'No sample requests selected'}), 400
        
        if not updates:
            return jsonify({'success': False, 'error': 'No updates provided'}), 400
        
        # Get sample requests
        samples = SampleRequest.query.filter(SampleRequest.request_id.in_(request_ids)).all()
        
        if not samples:
            return jsonify({'success': False, 'error': 'No valid sample requests found'}), 404
        
        updated_samples = []
        
        for sample in samples:
            # Store old values for audit
            old_values = sample.to_dict()
            
            # Apply updates
            if 'fulfillment_status' in updates:
                sample.fulfillment_status = updates['fulfillment_status']
            
            if 'shipped_date' in updates:
                if updates['shipped_date']:
                    sample.shipped_date = datetime.fromisoformat(updates['shipped_date'].replace('Z', '+00:00'))
                else:
                    sample.shipped_date = None
            
            if 'fulfilled_by' in updates:
                sample.fulfilled_by = updates['fulfilled_by']
            
            if 'fulfillment_notes' in updates:
                sample.fulfillment_notes = updates['fulfillment_notes']
            
            if 'shipping_carrier' in updates:
                sample.shipping_carrier = updates['shipping_carrier']
            
            # If status is being set to shipped, set shipped_date if not provided
            if updates.get('fulfillment_status') == 'shipped' and not sample.shipped_date:
                sample.shipped_date = datetime.utcnow()
            
            updated_samples.append(sample.to_dict())
            
            # Log the update
            AuditLog.log_action(
                user_id='system',  # TODO: Get from session
                action_type='bulk_update',
                table_name='sample_requests',
                record_id=sample.request_id,
                old_values=old_values,
                new_values=sample.to_dict(),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': len(updated_samples),
            'sample_requests': updated_samples
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/summary', methods=['GET'])
def get_samples_summary():
    """Get sample fulfillment statistics"""
    try:
        # Get counts by status
        total_requests = SampleRequest.query.count()
        pending_requests = SampleRequest.query.filter_by(fulfillment_status='pending').count()
        processing_requests = SampleRequest.query.filter_by(fulfillment_status='processing').count()
        shipped_requests = SampleRequest.query.filter_by(fulfillment_status='shipped').count()
        delivered_requests = SampleRequest.query.filter_by(fulfillment_status='delivered').count()
        cancelled_requests = SampleRequest.query.filter_by(fulfillment_status='cancelled').count()
        
        # Get recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_requests = SampleRequest.query.filter(
            SampleRequest.request_timestamp >= thirty_days_ago
        ).count()
        
        recent_shipped = SampleRequest.query.filter(
            SampleRequest.shipped_date >= thirty_days_ago
        ).count()
        
        # Get top campaigns by sample requests
        from sqlalchemy import func
        top_campaigns = db.session.query(
            Campaign.campaign_name,
            func.count(SampleRequest.request_id).label('request_count')
        ).join(
            SampleRequest, Campaign.campaign_id == SampleRequest.campaign_id
        ).group_by(
            Campaign.campaign_id, Campaign.campaign_name
        ).order_by(
            func.count(SampleRequest.request_id).desc()
        ).limit(5).all()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'processing_requests': processing_requests,
                'shipped_requests': shipped_requests,
                'delivered_requests': delivered_requests,
                'cancelled_requests': cancelled_requests,
                'recent_requests_30_days': recent_requests,
                'recent_shipped_30_days': recent_shipped,
                'top_campaigns': [
                    {'campaign_name': name, 'request_count': count}
                    for name, count in top_campaigns
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/export', methods=['GET'])
def export_sample_requests():
    """Export sample requests to CSV"""
    try:
        # Get filter parameters
        status = request.args.get('status')
        campaign_id = request.args.get('campaign_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = db.session.query(SampleRequest, Contact, Campaign).join(
            Contact, SampleRequest.contact_id == Contact.contact_id
        ).join(
            Campaign, SampleRequest.campaign_id == Campaign.campaign_id
        )
        
        # Apply filters
        if status:
            query = query.filter(SampleRequest.fulfillment_status == status)
        
        if campaign_id:
            query = query.filter(SampleRequest.campaign_id == campaign_id)
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(SampleRequest.request_timestamp >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(SampleRequest.request_timestamp <= date_to_obj)
            except ValueError:
                pass
        
        results = query.all()
        
        # Convert to CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Request ID', 'Contact ID', 'First Name', 'Last Name', 'Email Address',
            'Phone Number', 'Company Name', 'Campaign Name', 'Sample Type',
            'Quantity Requested', 'Quantity Shipped', 'Request Date', 'Fulfillment Status',
            'Shipped Date', 'Tracking Number', 'Shipping Carrier', 'Fulfilled By',
            'Fulfillment Cost', 'Fulfillment Notes', 'Address Line 1', 'Address Line 2',
            'City', 'State/Province', 'Postal Code', 'Country'
        ])
        
        # Write data
        for sample, contact, campaign in results:
            shipping_address = sample.get_shipping_address()
            
            writer.writerow([
                sample.request_id,
                contact.contact_id,
                contact.first_name,
                contact.last_name,
                contact.email_address,
                contact.phone_number,
                contact.company_name,
                campaign.campaign_name,
                sample.sample_type,
                sample.quantity_requested,
                sample.quantity_shipped,
                sample.request_timestamp.strftime('%Y-%m-%d %H:%M:%S') if sample.request_timestamp else '',
                sample.fulfillment_status,
                sample.shipped_date.strftime('%Y-%m-%d %H:%M:%S') if sample.shipped_date else '',
                sample.tracking_number,
                sample.shipping_carrier,
                sample.fulfilled_by,
                float(sample.fulfillment_cost) if sample.fulfillment_cost else '',
                sample.fulfillment_notes,
                shipping_address.get('line1', ''),
                shipping_address.get('line2', ''),
                shipping_address.get('city', ''),
                shipping_address.get('state', ''),
                shipping_address.get('postal_code', ''),
                shipping_address.get('country', '')
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sample_requests_export.csv'}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@samples_bp.route('/samples/shipping-labels', methods=['POST'])
def generate_shipping_labels():
    """Generate shipping labels for selected sample requests"""
    try:
        data = request.get_json()
        request_ids = data.get('request_ids', [])
        
        if not request_ids:
            return jsonify({'success': False, 'error': 'No sample requests selected'}), 400
        
        # Get sample requests with contact and shipping info
        results = db.session.query(SampleRequest, Contact).join(
            Contact, SampleRequest.contact_id == Contact.contact_id
        ).filter(SampleRequest.request_id.in_(request_ids)).all()
        
        if not results:
            return jsonify({'success': False, 'error': 'No valid sample requests found'}), 404
        
        # Generate label data (in a real application, this would integrate with shipping APIs)
        labels = []
        for sample, contact in results:
            shipping_address = sample.get_shipping_address()
            
            # Use contact address if no shipping address specified
            if not shipping_address:
                shipping_address = {
                    'line1': contact.address_line1,
                    'line2': contact.address_line2,
                    'city': contact.city,
                    'state': contact.state_province,
                    'postal_code': contact.postal_code,
                    'country': contact.country
                }
            
            label_data = {
                'request_id': sample.request_id,
                'recipient': {
                    'name': f"{contact.first_name} {contact.last_name}",
                    'company': contact.company_name,
                    'address': shipping_address
                },
                'sample_type': sample.sample_type,
                'quantity': sample.quantity_requested,
                'tracking_number': sample.tracking_number or f"TRACK{sample.request_id:06d}"
            }
            
            labels.append(label_data)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'message': f'Generated {len(labels)} shipping labels'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

