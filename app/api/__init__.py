from flask import Blueprint, jsonify
from app.api.metrics import metrics_bp

discord_bp = Blueprint('discord', __name__, url_prefix='/discord')

@discord_bp.route('/users/<user_id>/avatar', methods=['GET'])
def get_avatar(user_id):
    """Proxy Discord CDN avatar."""
    # This will be implemented for CDN proxy functionality
    return jsonify({"error": "Not implemented"}), 501
