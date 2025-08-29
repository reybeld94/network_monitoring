from flask import Blueprint, request, jsonify
from ..services.agent_service import AgentService
from ..services.data_service import DataService

agents_bp = Blueprint('agents', __name__, url_prefix='/api/agents')
_agent_service = AgentService()
_data_service = DataService()


@agents_bp.route('/register', methods=['POST'])
def register_agent():
    data = request.get_json(force=True)
    if 'agent_id' not in data:
        return jsonify({'error': 'agent_id is required'}), 400
    agent = _agent_service.register_agent(data, request.remote_addr)
    return jsonify({'agent_id': agent.agent_id})


@agents_bp.route('/monitoring-data', methods=['POST'])
def monitoring_data():
    data = request.get_json(force=True)
    agent_id = data.get('system', {}).get('agent_id')
    if not agent_id:
        return jsonify({'error': 'system.agent_id is required'}), 400
    _data_service.store_monitoring_data(agent_id, data)
    return jsonify({'status': 'ok'})


@agents_bp.route('/service-tag/<service_tag>', methods=['GET'])
def get_agent_by_service_tag(service_tag):
    agent = _agent_service.get_by_service_tag(service_tag)
    if not agent:
        return jsonify({'error': 'agent not found'}), 404
    payload = {
        'agent_id': agent.agent_id,
        'hostname': agent.hostname,
        'service_tag': agent.service_tag,
        'manufacturer': agent.manufacturer,
        'model': agent.model,
        'detection_method': agent.detection_method,
        'hardware_info': {
            'service_tag': agent.service_tag,
            'serial_number': agent.serial_number,
            'manufacturer': agent.manufacturer,
            'model': agent.model,
        },
    }
    return jsonify(payload)
