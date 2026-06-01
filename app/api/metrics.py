from flask import Blueprint, jsonify
from prometheus_client import generate_latest

metrics_bp = Blueprint('metrics', __name__, url_prefix='/metrics')

@metrics_bp.route('', methods=['GET'])
def metrics():
    """Return Prometheus metrics."""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
