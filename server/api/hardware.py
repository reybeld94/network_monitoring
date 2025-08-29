from flask import Blueprint, jsonify
from ..models import db, Agent

hardware_bp = Blueprint('hardware', __name__, url_prefix='/api/hardware')


@hardware_bp.route('/', methods=['GET'])
def get_hardware_overview():
    """Return a simple overview of hardware information."""
    manufacturer_counts = (
        db.session.query(Agent.manufacturer, db.func.count(Agent.id))
        .group_by(Agent.manufacturer)
        .all()
    )
    model_counts = (
        db.session.query(Agent.model, db.func.count(Agent.id))
        .group_by(Agent.model)
        .all()
    )
    service_tags = (
        db.session.query(db.func.count(Agent.service_tag))
        .filter(Agent.service_tag.isnot(None))
        .scalar()
    )
    total = db.session.query(db.func.count(Agent.id)).scalar()
    return jsonify(
        {
            "manufacturers": {m or "Unknown": c for m, c in manufacturer_counts},
            "models": {m or "Unknown": c for m, c in model_counts},
            "service_tags": service_tags,
            "systems": total,
        }
    )
