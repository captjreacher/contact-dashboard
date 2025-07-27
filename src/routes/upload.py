from flask import Blueprint, request, jsonify, current_app
import pandas as pd
import uuid
import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from src.models.models import db
from src.models.models import Contact, UploadBatch, ValidationRule
from src.models.models import AuditLog
import json

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

import phonenumbers

def validate_phone(phone):
    """Validate and standardize phone number using phonenumbers library"""
    if not phone:
        return True, phone
    
    try:
        # Parse the phone number
        parsed_number = phonenumbers.parse(phone, None)

        # Check if the number is valid
        if not phonenumbers.is_valid_number(parsed_number):
            return False, phone

        # Format the number in E.164 format
        formatted_number = phonenumbers.format_number(
            parsed_number, phonenumbers.PhoneNumberFormat.E164
        )

        return True, formatted_number

    except phonenumbers.phonenumberutil.NumberParseException:
        return False, phone

def validate_required_fields(row):
    """Validate required fields"""
    errors = []
    
    if not row.get('first_name') or str(row['first_name']).strip() == '':
        errors.append('First name is required')
    
    if not row.get('last_name') or str(row['last_name']).strip() == '':
        errors.append('Last name is required')
    
    if not row.get('email_address') or str(row['email_address']).strip() == '':
        errors.append('Email address is required')
    
    return errors

def validate_contact_data(row):
    """Validate a single contact row"""
    errors = []
    
    # Required field validation
    errors.extend(validate_required_fields(row))
    
    # Email validation
    if row.get('email_address'):
        if not validate_email(str(row['email_address']).strip()):
            errors.append('Invalid email format')
    
    # Phone validation
    if row.get('phone_number'):
        is_valid, formatted_phone = validate_phone(str(row['phone_number']))
        if not is_valid:
            errors.append('Invalid phone number format')
        else:
            row['phone_number'] = formatted_phone
    
    return errors, row

def detect_duplicates(df):
    """Detect duplicate contacts based on email address (case-insensitive)"""
    df['email_lower'] = df['email_address'].str.lower()
    duplicates = df[df.duplicated(subset=['email_lower'], keep=False)]
    return duplicates

def process_spreadsheet(file_path, batch_id, validation_rules=None):
    """Process uploaded spreadsheet and validate data"""
    try:
        # Read the file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Required columns mapping
        required_columns = {
            'first_name': ['first_name', 'firstname', 'fname'],
            'last_name': ['last_name', 'lastname', 'lname'],
            'email_address': ['email_address', 'email', 'email_addr']
        }
        
        # Map columns to standard names
        for standard_name, possible_names in required_columns.items():
            for col in df.columns:
                if col in possible_names:
                    df.rename(columns={col: standard_name}, inplace=True)
                    break
        
        total_records = len(df)
        valid_records = 0
        invalid_records = 0
        duplicate_records = 0
        
        # Detect duplicates
        duplicates_df = detect_duplicates(df)
        duplicate_emails = set(duplicates_df['email_lower'].tolist())
        
        # Process each row
        for index, row in df.iterrows():
            errors, validated_row = validate_contact_data(row.to_dict())
            
            # Check if duplicate
            is_duplicate = row['email_address'].lower() in duplicate_emails
            
            if is_duplicate:
                validation_status = 'duplicate'
                duplicate_records += 1
            elif errors:
                validation_status = 'invalid'
                invalid_records += 1
            else:
                validation_status = 'valid'
                valid_records += 1
            
            # Create contact record
            contact = Contact(
                upload_batch_id=batch_id,
                first_name=validated_row.get('first_name', '').strip(),
                last_name=validated_row.get('last_name', '').strip(),
                email_address=validated_row.get('email_address', '').strip().lower(),
                phone_number=validated_row.get('phone_number'),
                company_name=validated_row.get('company_name'),
                job_title=validated_row.get('job_title'),
                address_line1=validated_row.get('address_line1'),
                address_line2=validated_row.get('address_line2'),
                city=validated_row.get('city'),
                state_province=validated_row.get('state_province'),
                postal_code=validated_row.get('postal_code'),
                country=validated_row.get('country'),
                validation_status=validation_status,
                validation_errors=json.dumps(errors) if errors else None
            )
            
            db.session.add(contact)
        
        # Update batch record
        batch = UploadBatch.query.get(batch_id)
        batch.total_records = total_records
        batch.valid_records = valid_records
        batch.invalid_records = invalid_records
        batch.duplicate_records = duplicate_records
        batch.processing_status = 'completed'
        
        db.session.commit()
        
        return {
            'success': True,
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': invalid_records,
            'duplicate_records': duplicate_records
        }
        
    except Exception as e:
        # Update batch with error
        batch = UploadBatch.query.get(batch_id)
        batch.processing_status = 'failed'
        batch.processing_errors = json.dumps([str(e)])
        db.session.commit()
        
        return {
            'success': False,
            'error': str(e)
        }

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process contact spreadsheet"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload CSV or Excel files.'}), 400
        
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        
        # Save file
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, f"{batch_id}_{filename}")
        file.save(file_path)
        
        # Create batch record
        batch = UploadBatch(
            batch_id=batch_id,
            filename=filename,
            file_size=os.path.getsize(file_path),
            total_records=0,  # Will be updated during processing
            processing_status='processing',
            uploaded_by='system'  # TODO: Get from session
        )
        
        db.session.add(batch)
        db.session.commit()
        
        # Process file (in a real application, this would be done asynchronously)
        result = process_spreadsheet(file_path, batch_id)
        
        # Clean up file
        os.remove(file_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'batch_id': batch_id,
                'processing_status': 'completed',
                'total_records': result['total_records'],
                'valid_records': result['valid_records'],
                'invalid_records': result['invalid_records'],
                'duplicate_records': result['duplicate_records']
            })
        else:
            batch = UploadBatch.query.get(batch_id)
            return jsonify({
                'success': False,
                'batch_id': batch_id,
                'error': 'Processing failed',
                'processing_errors': json.loads(batch.processing_errors) if batch.processing_errors else []
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/upload/<batch_id>/status', methods=['GET'])
def get_upload_status(batch_id):
    """Get processing status of uploaded file"""
    try:
        batch = UploadBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        return jsonify({
            'batch_id': batch_id,
            'status': batch.processing_status,
            'progress': {
                'total_records': batch.total_records,
                'processed_records': batch.total_records,  # Since we process synchronously
                'valid_records': batch.valid_records,
                'invalid_records': batch.invalid_records,
                'duplicate_records': batch.duplicate_records
            },
            'validation_summary': {
                'email_format_errors': 0,  # TODO: Calculate from validation errors
                'missing_required_fields': 0,
                'phone_format_errors': 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/upload/<batch_id>/errors', methods=['GET'])
def get_upload_errors(batch_id):
    """Get detailed validation errors for a batch"""
    try:
        batch = UploadBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404

        errors = []
        contacts = Contact.query.filter_by(upload_batch_id=batch_id, validation_status='invalid').all()

        for contact in contacts:
            errors.append({
                'line_number': contact.id,  # Or some other way to identify the row
                'email_address': contact.email_address,
                'errors': json.loads(contact.validation_errors)
            })

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'errors': errors
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/upload/<batch_id>/results', methods=['GET'])
def get_upload_results(batch_id):
    """Get detailed validation results"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        filter_type = request.args.get('filter', 'all')
        
        batch = UploadBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        # Build query
        query = Contact.query.filter_by(upload_batch_id=batch_id)
        
        if filter_type != 'all':
            query = query.filter_by(validation_status=filter_type)
        
        # Paginate results
        contacts = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'batch_id': batch_id,
            'total_records': contacts.total,
            'page': page,
            'per_page': per_page,
            'total_pages': contacts.pages,
            'records': [contact.to_summary_dict() for contact in contacts.items]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@upload_bp.route('/upload/batches', methods=['GET'])
def get_upload_batches():
    """Get list of upload batches"""
    try:
        batches = UploadBatch.query.order_by(UploadBatch.upload_timestamp.desc()).all()
        return jsonify({
            'success': True,
            'batches': [batch.to_dict() for batch in batches]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

