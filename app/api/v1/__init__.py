from flask import Blueprint, request, jsonify
from services.presence import get_pretty_presence
from services.kv_store import set as kv_set, delete as kv_delete, multiset as kv_multiset
from services.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

v1_bp = Blueprint('v1', __name__, url_prefix='/v1')

@v1_bp.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user presence by ID."""
    status, data = get_pretty_presence(user_id)
    return jsonify(data), status

@v1_bp.route('/users/@me', methods=['GET'])
def get_me():
    """Get current user presence (requires API key)."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"success": False, "error": "Missing authorization header"}), 401

    user_id = redis_client.get(f"api_key:{auth_header}")
    if not user_id:
        return jsonify({"success": False, "error": "Invalid API key"}), 401

    status, data = get_pretty_presence(user_id)
    return jsonify(data), status

@v1_bp.route('/users/<user_id>/kv/<field>', methods=['PUT'])
def set_kv(user_id, field):
    """Set a KV pair."""
    if not validate_resource_access(user_id):
        return jsonify({"success": False, "error": "Forbidden"}), 403

    value = request.get_data(as_text=True)
    success, error = kv_set(user_id, field, value)

    if not success:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True}), 200

@v1_bp.route('/users/<user_id>/kv', methods=['PATCH'])
def patch_kv(user_id):
    """Set multiple KV pairs."""
    if not validate_resource_access(user_id):
        return jsonify({"success": False, "error": "Forbidden"}), 403

    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Body must be an object"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": "Invalid JSON"}), 400

    success, error = kv_multiset(user_id, data)
    if not success:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True}), 200

@v1_bp.route('/users/<user_id>/kv/<field>', methods=['DELETE'])
def delete_kv(user_id, field):
    """Delete a KV pair."""
    if not validate_resource_access(user_id):
        return jsonify({"success": False, "error": "Forbidden"}), 403

    success, error = kv_delete(user_id, field)
    if not success:
        return jsonify({"success": False, "error": error}), 404

    return jsonify({"success": True}), 200

def validate_resource_access(user_id: str) -> bool:
    """Validate if the request has access to this user's resources."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False

    stored_user_id = redis_client.get(f"api_key:{auth_header}")
    return stored_user_id == user_id
