import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.app import create_app


def test_app_factory():
    app = create_app()
    assert app.testing is False
    client = app.test_client()
    resp = client.get('/api/hardware/')
    assert resp.status_code == 200


def test_dashboard_route():
    app = create_app()
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'System Monitor' in resp.data
