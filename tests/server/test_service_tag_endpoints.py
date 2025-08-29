import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.app import create_app
from server.config.server_config import ServerConfig
from server.models import db, Agent


def create_test_app():
    return create_app(ServerConfig(database_uri="sqlite:///:memory:"))


def test_register_agent_with_service_tag():
    app = create_test_app()
    client = app.test_client()
    payload = {
        'agent_id': 'HOST1',
        'hostname': 'HOST1',
        'service_tag': 'ST123',
        'serial_number': 'ST123',
        'manufacturer': 'Dell',
        'model': 'OptiPlex',
        'detection_method': 'wmic',
    }
    resp = client.post('/api/agents/register', json=payload)
    assert resp.status_code == 200
    with app.app_context():
        agent = Agent.query.filter_by(service_tag='ST123').first()
        assert agent is not None
        assert agent.manufacturer == 'Dell'


def test_search_by_service_tag():
    app = create_test_app()
    client = app.test_client()
    with app.app_context():
        agent = Agent(agent_id='HOST2', service_tag='XYZ789', hostname='HOST2')
        db.session.add(agent)
        db.session.commit()
    resp = client.get('/api/agents/service-tag/XYZ789')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['service_tag'] == 'XYZ789'
    search_resp = client.get('/api/search', query_string={'q': 'XYZ789'})
    assert search_resp.status_code == 200
    assert search_resp.get_json()['results'][0]['service_tag'] == 'XYZ789'
