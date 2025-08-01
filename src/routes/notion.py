from flask import Blueprint, request, jsonify
from src.services.notion_helper import NotionHelper

notion_bp = Blueprint('notion', __name__, url_prefix='/api/integrations/notion')

# --- OAuth Connect (stub) ---
@notion_bp.route('/connect', methods=['POST'])
def connect_to_notion():
    # TODO: Implement OAuth handshake with Notion
    # For now, just return a dummy response
    return jsonify({"success": True, "message": "OAuth connection not implemented yet."})

# --- Fetch Notion Contacts ---
@notion_bp.route('/contacts', methods=['GET'])
def get_notion_contacts():
    # Example: fetch contacts from Notion using the helper
    notion = NotionHelper()
    contacts = notion.fetch_contacts()
    return jsonify({"contacts": contacts})
