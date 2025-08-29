from flask import Blueprint, jsonify
from ..models import db, Agent

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


@statistics_bp.route('/', methods=['GET'])
def stats():
    """Placeholder statistics endpoint."""
    return jsonify({})


@statistics_bp.route('/hardware', methods=['GET'])
def get_hardware_stats():
    """Return basic hardware statistics."""
    manufacturer_counts = (
        db.session.query(Agent.manufacturer, db.func.count(Agent.id))
        .group_by(Agent.manufacturer)
        .all()
    )
    total = db.session.query(db.func.count(Agent.id)).scalar()
    detected = (
        db.session.query(db.func.count(Agent.service_tag))
        .filter(Agent.service_tag.isnot(None))
        .scalar()
    )
    return jsonify(
        {
            "manufacturers": {m or "Unknown": c for m, c in manufacturer_counts},
            "detection_success": detected,
            "detection_failed": total - detected,
            "total": total,
        }
    )
