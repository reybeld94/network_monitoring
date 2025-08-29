from flask import Blueprint, jsonify

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


@statistics_bp.route('/', methods=['GET'])
def stats():
    """Placeholder statistics endpoint."""
    return jsonify({})
