import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.app import create_app
from server.config.server_config import ServerConfig


def create_test_app():
    return create_app(ServerConfig(database_uri="sqlite:///:memory:"))


def test_agents_history_endpoint():
    app = create_test_app()
    client = app.test_client()

    register_payload = {
        "agent_id": "AGENT1",
        "hostname": "HOST1",
    }
    client.post("/api/agents/register", json=register_payload)

    monitoring_payload = {
        "system": {"agent_id": "AGENT1"},
        "backup": {
            "status": "found",
            "backup_location": "/data/backup",
        },
    }
    client.post("/api/agents/monitoring-data", json=monitoring_payload)

    resp = client.get("/api/agents/history")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "agents" in data
    assert len(data["agents"]) == 1
    agent = data["agents"][0]
    assert agent["agent_id"] == "AGENT1"
    assert agent["backup"]["status"] == "found"
