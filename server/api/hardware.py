from flask import Blueprint, jsonify

hardware_bp = Blueprint('hardware', __name__, url_prefix='/api/hardware')


@hardware_bp.route('/', methods=['GET'])
def list_hardware():
    """Placeholder endpoint returning an empty list."""
    return jsonify([])
