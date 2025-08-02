from flask import Blueprint, request, jsonify, abort
from src.models.models import db, WebhookConfig  # Adjust import path if needed

webhookconfig_bp = Blueprint('webhookconfig', __name__, url_prefix='/api/webhooks')

@webhookconfig_bp.route('', methods=['GET'])
def get_webhooks():
    webhooks = WebhookConfig.query.all()
    return jsonify([{
        'id': w.id,
        'url': w.url,
        'events': w.events,    # Adjust if stored as string: split or parse JSON
        'headers': w.headers,  # JSON string
    } for w in webhooks])

@webhookconfig_bp.route('', methods=['POST'])
def create_webhook():
    data = request.get_json()
    if not data or not data.get('url') or not data.get('events'):
        abort(400, 'Missing required fields')
    
    # If events is a string, convert to list or store as needed
    events = data['events']
    if isinstance(events, str):
        events = [e.strip() for e in events.split(',')]
    
    new_webhook = WebhookConfig(
        url=data['url'],
        events=events,
        headers=data.get('headers', '{}')
    )
    db.session.add(new_webhook)
    db.session.commit()

    return jsonify({
        'id': new_webhook.id,
        'url': new_webhook.url,
        'events': new_webhook.events,
        'headers': new_webhook.headers,
    }), 201

@webhookconfig_bp.route('/<int:webhook_id>', methods=['PUT'])
def update_webhook(webhook_id):
    webhook = WebhookConfig.query.get_or_404(webhook_id)
    data = request.get_json()
    if not data or not data.get('url') or not data.get('events'):
        abort(400, 'Missing required fields')
    
    events = data['events']
    if isinstance(events, str):
        events = [e.strip() for e in events.split(',')]
    
    webhook.url = data['url']
    webhook.events = events
    webhook.headers = data.get('headers', '{}')
    db.session.commit()

    return jsonify({
        'id': webhook.id,
        'url': webhook.url,
        'events': webhook.events,
        'headers': webhook.headers,
    })

@webhookconfig_bp.route('/<int:webhook_id>', methods=['DELETE'])
def delete_webhook(webhook_id):
    webhook = WebhookConfig.query.get_or_404(webhook_id)
    db.session.delete(webhook)
    db.session.commit()
    return '', 204
