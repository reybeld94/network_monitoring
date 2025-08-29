from flask import Blueprint, jsonify

software_bp = Blueprint('software', __name__, url_prefix='/api/software')


@software_bp.route('/', methods=['GET'])
def list_software():
    """Placeholder endpoint returning an empty list."""
    return jsonify([])
