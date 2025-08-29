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
