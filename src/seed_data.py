#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for testing
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import uuid
import json
from src.models.models import db, Contact, UploadBatch, ValidationRule, Campaign, CampaignResult, CampaignJob, SampleRequest, AuditLog
from src.main import app

def create_sample_validation_rules():
    """Create sample validation rules"""
    rules = [
        ValidationRule(
            rule_name='Email Required',
            rule_type='required_field',
            field_name='email_address',
            error_message='Email address is required',
            is_active=True,
            rule_order=1
        ),
        ValidationRule(
            rule_name='First Name Required',
            rule_type='required_field',
            field_name='first_name',
            error_message='First name is required',
            is_active=True,
            rule_order=2
        ),
        ValidationRule(
            rule_name='Last Name Required',
            rule_type='required_field',
            field_name='last_name',
            error_message='Last name is required',
            is_active=True,
            rule_order=3
        ),
        ValidationRule(
            rule_name='Email Format',
            rule_type='format_validation',
            field_name='email_address',
            validation_pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            error_message='Invalid email format',
            is_active=True,
            rule_order=4
        )
    ]
    
    for rule in rules:
        db.session.add(rule)
    
    print(f"Created {len(rules)} validation rules")

def create_sample_campaign_jobs():
    """Create sample campaign jobs"""
    jobs = [
        CampaignJob(
            job_name='product_launch_email',
            job_description='Product launch email campaign with sample request tracking',
            webhook_url='https://hook.make.com/scenario123',
            make_scenario_id='scenario_123',
            created_by='admin',
            is_active=True
        ),
        CampaignJob(
            job_name='newsletter_signup',
            job_description='Newsletter signup confirmation and welcome series',
            webhook_url='https://hook.make.com/scenario456',
            make_scenario_id='scenario_456',
            created_by='admin',
            is_active=True
        ),
        CampaignJob(
            job_name='follow_up_sequence',
            job_description='Follow-up email sequence for prospects',
            webhook_url='https://hook.make.com/scenario789',
            make_scenario_id='scenario_789',
            created_by='admin',
            is_active=True
        )
    ]
    
    # Set job parameters
    jobs[0].set_job_parameters([
        {
            'name': 'product_name',
            'type': 'string',
            'required': True,
            'description': 'Name of the product being launched'
        },
        {
            'name': 'launch_date',
            'type': 'date',
            'required': True,
            'description': 'Product launch date'
        }
    ])
    
    jobs[1].set_job_parameters([
        {
            'name': 'newsletter_type',
            'type': 'string',
            'required': True,
            'description': 'Type of newsletter (weekly, monthly)'
        }
    ])
    
    jobs[2].set_job_parameters([
        {
            'name': 'follow_up_days',
            'type': 'integer',
            'required': True,
            'description': 'Number of days between follow-ups'
        }
    ])
    
    for job in jobs:
        db.session.add(job)
    
    print(f"Created {len(jobs)} campaign jobs")

def create_sample_upload_batch():
    """Create sample upload batch"""
    batch_id = str(uuid.uuid4())
    batch = UploadBatch(
        batch_id=batch_id,
        filename='sample_contacts.csv',
        file_size=15420,
        total_records=50,
        valid_records=45,
        invalid_records=3,
        duplicate_records=2,
        processing_status='completed',
        uploaded_by='admin',
        upload_timestamp=datetime.utcnow() - timedelta(days=2)
    )
    
    db.session.add(batch)
    print(f"Created upload batch: {batch_id}")
    return batch_id

def create_sample_contacts(batch_id):
    """Create sample contacts"""
    sample_contacts = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email_address': 'john.doe@acmecorp.com',
            'phone_number': '+1-555-0123',
            'company_name': 'Acme Corporation',
            'job_title': 'Marketing Manager',
            'address_line1': '123 Business Ave',
            'city': 'New York',
            'state_province': 'NY',
            'postal_code': '10001',
            'country': 'USA',
            'validation_status': 'valid',
            'email_verification_status': 'valid'
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email_address': 'jane.smith@techstart.com',
            'phone_number': '+1-555-0456',
            'company_name': 'TechStart Inc',
            'job_title': 'Product Manager',
            'address_line1': '456 Innovation Dr',
            'city': 'San Francisco',
            'state_province': 'CA',
            'postal_code': '94105',
            'country': 'USA',
            'validation_status': 'valid',
            'email_verification_status': 'valid'
        },
        {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'email_address': 'bob.johnson@manufacturing.com',
            'phone_number': '+1-555-0789',
            'company_name': 'Johnson Manufacturing',
            'job_title': 'Operations Director',
            'address_line1': '789 Industrial Blvd',
            'city': 'Chicago',
            'state_province': 'IL',
            'postal_code': '60601',
            'country': 'USA',
            'validation_status': 'valid',
            'email_verification_status': 'valid'
        },
        {
            'first_name': 'Alice',
            'last_name': 'Williams',
            'email_address': 'alice.williams@consulting.com',
            'phone_number': '+1-555-0321',
            'company_name': 'Williams Consulting',
            'job_title': 'Senior Consultant',
            'address_line1': '321 Professional Way',
            'city': 'Boston',
            'state_province': 'MA',
            'postal_code': '02101',
            'country': 'USA',
            'validation_status': 'valid',
            'email_verification_status': 'valid'
        },
        {
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'email_address': 'charlie.brown@invalid-domain.xyz',
            'phone_number': '+1-555-9999',
            'company_name': 'Test Company',
            'job_title': 'Test Manager',
            'address_line1': '999 Test St',
            'city': 'Test City',
            'state_province': 'TC',
            'postal_code': '99999',
            'country': 'USA',
            'validation_status': 'invalid',
            'email_verification_status': 'invalid'
        }
    ]
    
    contacts = []
    for i, contact_data in enumerate(sample_contacts):
        contact = Contact(
            upload_batch_id=batch_id,
            **contact_data,
            created_timestamp=datetime.utcnow() - timedelta(days=2, hours=i)
        )
        
        if contact.email_verification_status == 'valid':
            contact.email_verification_date = datetime.utcnow() - timedelta(days=1)
            contact.email_verification_details = json.dumps({
                'deliverable': True,
                'risk_level': 'low',
                'provider': contact.email_address.split('@')[1]
            })
        elif contact.email_verification_status == 'invalid':
            contact.email_verification_date = datetime.utcnow() - timedelta(days=1)
            contact.email_verification_details = json.dumps({
                'deliverable': False,
                'risk_level': 'high',
                'provider': contact.email_address.split('@')[1]
            })
        
        contacts.append(contact)
        db.session.add(contact)
    
    print(f"Created {len(contacts)} sample contacts")
    return contacts

def create_sample_campaign(contacts):
    """Create sample campaign with results"""
    # Create campaign
    campaign = Campaign(
        campaign_name='Q1 Product Launch Campaign',
        job_name='product_launch_email',
        job_webhook_url='https://hook.make.com/scenario123',
        campaign_description='Launch campaign for our new product line',
        total_contacts=3,
        processed_contacts=3,
        successful_contacts=2,
        failed_contacts=1,
        campaign_status='completed',
        execution_start_time=datetime.utcnow() - timedelta(hours=6),
        execution_end_time=datetime.utcnow() - timedelta(hours=5),
        created_by='admin',
        make_scenario_id='scenario_123',
        created_timestamp=datetime.utcnow() - timedelta(days=1)
    )
    
    # Set selected contacts (first 3 valid contacts)
    valid_contacts = [c for c in contacts if c.validation_status == 'valid'][:3]
    campaign.set_selected_contact_ids([c.contact_id for c in valid_contacts])
    
    # Set campaign settings
    campaign.set_campaign_settings({
        'product_name': 'Widget Pro',
        'launch_date': '2024-02-01',
        'send_delay_seconds': 30
    })
    
    db.session.add(campaign)
    db.session.flush()  # Get campaign ID
    
    # Create campaign results
    results = []
    for i, contact in enumerate(valid_contacts):
        status = 'delivered' if i < 2 else 'failed'
        sample_requested = i == 0  # First contact requests sample
        
        result = CampaignResult(
            campaign_id=campaign.campaign_id,
            contact_id=contact.contact_id,
            processing_status=status,
            sample_requested=sample_requested,
            processed_timestamp=datetime.utcnow() - timedelta(hours=5, minutes=i*10),
            delivery_timestamp=datetime.utcnow() - timedelta(hours=4, minutes=i*10) if status == 'delivered' else None
        )
        
        if status == 'delivered':
            result.set_make_response({
                'scenario_execution_id': f'exec_{campaign.campaign_id}_{contact.contact_id}',
                'status': 'success'
            })
            result.set_response_data({
                'email_opened': True,
                'links_clicked': ['product_info'] + (['sample_request'] if sample_requested else []),
                'engagement_score': 85 if sample_requested else 70
            })
        else:
            result.error_message = 'Email delivery failed - invalid recipient'
        
        results.append(result)
        db.session.add(result)
    
    db.session.flush()  # Get result IDs
    
    # Create sample request for the first contact
    if results[0].sample_requested:
        sample_request = SampleRequest(
            contact_id=valid_contacts[0].contact_id,
            campaign_id=campaign.campaign_id,
            result_id=results[0].result_id,
            sample_type='Widget Pro Sample Kit',
            quantity_requested=1,
            fulfillment_status='pending',
            request_timestamp=datetime.utcnow() - timedelta(hours=4)
        )
        
        # Set shipping address
        contact = valid_contacts[0]
        sample_request.set_shipping_address({
            'line1': contact.address_line1,
            'line2': contact.address_line2,
            'city': contact.city,
            'state': contact.state_province,
            'postal_code': contact.postal_code,
            'country': contact.country
        })
        
        db.session.add(sample_request)
    
    print(f"Created campaign '{campaign.campaign_name}' with {len(results)} results")
    return campaign

def create_audit_logs():
    """Create sample audit logs"""
    logs = [
        AuditLog(
            user_id='admin',
            action_type='create',
            table_name='campaigns',
            record_id=1,
            timestamp=datetime.utcnow() - timedelta(days=1),
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ),
        AuditLog(
            user_id='admin',
            action_type='update',
            table_name='contacts',
            record_id=1,
            timestamp=datetime.utcnow() - timedelta(hours=12),
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ),
        AuditLog(
            user_id='webhook',
            action_type='webhook_received',
            table_name='campaign_results',
            record_id=1,
            timestamp=datetime.utcnow() - timedelta(hours=4),
            ip_address='10.0.0.1',
            user_agent='Make.com Webhook'
        )
    ]
    
    for log in logs:
        db.session.add(log)
    
    print(f"Created {len(logs)} audit log entries")

def seed_database():
    """Main function to seed the database with sample data"""
    print("Starting database seeding...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        try:
            db.session.query(AuditLog).delete()
            db.session.query(SampleRequest).delete()
            db.session.query(CampaignResult).delete()
            db.session.query(Campaign).delete()
            db.session.query(Contact).delete()
            db.session.query(UploadBatch).delete()
            db.session.query(CampaignJob).delete()
            db.session.query(ValidationRule).delete()
            db.session.commit()
        except Exception as e:
            print(f"Note: Some tables may not exist yet: {e}")
            db.session.rollback()
        
        # Create sample data
        create_sample_validation_rules()
        create_sample_campaign_jobs()
        batch_id = create_sample_upload_batch()
        contacts = create_sample_contacts(batch_id)
        
        # Commit contacts first to get IDs
        db.session.commit()
        
        # Create campaign and related data
        campaign = create_sample_campaign(contacts)
        create_audit_logs()
        
        # Final commit
        db.session.commit()
        
        print("Database seeding completed successfully!")
        print("\nSample data created:")
        print(f"- {ValidationRule.query.count()} validation rules")
        print(f"- {CampaignJob.query.count()} campaign jobs")
        print(f"- {UploadBatch.query.count()} upload batches")
        print(f"- {Contact.query.count()} contacts")
        print(f"- {Campaign.query.count()} campaigns")
        print(f"- {CampaignResult.query.count()} campaign results")
        print(f"- {SampleRequest.query.count()} sample requests")
        print(f"- {AuditLog.query.count()} audit log entries")

if __name__ == '__main__':
    seed_database()

