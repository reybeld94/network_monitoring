from flask import Blueprint, request, jsonify
from ..services.agent_service import AgentService

search_bp = Blueprint('search', __name__, url_prefix='/api')
_agent_service = AgentService()


@search_bp.route('/search', methods=['GET'])
def search_systems():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'q parameter required'}), 400
    agents = _agent_service.search(query)
    results = [
        {
            'agent_id': a.agent_id,
            'hostname': a.hostname,
            'service_tag': a.service_tag,
            'serial_number': a.serial_number,
            'manufacturer': a.manufacturer,
            'model': a.model,
        }
        for a in agents
    ]
    return jsonify({'results': results})
