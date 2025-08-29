import os
import os
import sys
from unittest.mock import patch, Mock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from client.detectors.hardware_detector import HardwareDetector


def test_service_tag_detection_wmic():
    detector = HardwareDetector(debug_mode=True)

    def run_side_effect(cmd, capture_output, text, timeout, check):  # noqa: ARG001
        if "computersystem" in cmd:
            return Mock(stdout="Node,Manufacturer,Model,Name\r\nHOST,Dell Inc.,OptiPlex 7090,HOST\r\n")
        if "bios" in cmd:
            return Mock(stdout="Node,SerialNumber\r\nHOST,1A2B3C4\r\n")
        return Mock(stdout="Node,SerialNumber\r\nHOST,ZZZ\r\n")

    with patch('subprocess.run', side_effect=run_side_effect):
        info = detector.get_service_tag_wmic()
    assert info['service_tag'] == '1A2B3C4'
    assert info['manufacturer'] == 'Dell Inc.'
    assert info['model'] == 'OptiPlex 7090'
    assert info['detection_method'] == 'wmic'


def test_service_tag_fallback():
    detector = HardwareDetector(debug_mode=True)

    def run_side_effect(cmd, capture_output, text, timeout, check):  # noqa: ARG001
        if cmd[0] == 'wmic':
            raise FileNotFoundError
        return Mock(stdout="HP,ProDesk 600,ABC123,XYZ789")

    with patch('subprocess.run', side_effect=run_side_effect):
        info = detector.get_service_tag()
    assert info['service_tag'] == 'ABC123'
    assert info['detection_method'] == 'powershell'
