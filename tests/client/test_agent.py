import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from client.core.agent import MonitoringAgent


def test_agent_creation():
    agent = MonitoringAgent(debug_mode=True)
    assert agent.hardware.detect()
    assert agent.software.detect() is not None
    assert agent.backup.detect() is not None
