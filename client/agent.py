import requests
import json
import time
import socket
import platform
import uuid
import subprocess
import re
from datetime import datetime
import os


class MonitoringAgent:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.agent_id = self.generate_agent_id()
        self.is_registered = False

    def generate_agent_id(self):
        hostname = socket.gethostname()
        mac = hex(uuid.getnode())[2:]
        return f"{hostname}_{mac}"

    def get_system_info(self):
        return {
            'agent_id': self.agent_id,
            'hostname': socket.gethostname(),
            'os': f"{platform.system()} {platform.release()}",
            'platform': platform.platform()
        }

    def get_backup_info(self):
        """Obtiene información de backups usando wbadmin"""
        backup_info = {
            'versions': [],
            'last_backup': None,
            'backup_location': None,
            'status': 'unknown'
        }

        try:
            # Ejecutar wbadmin get versions
            result = subprocess.run(
                ['wbadmin', 'get', 'versions'],
                capture_output=True,
                text=True,
                shell=True
            )
            print(f"🔍 ospp.vbs output found, parsing...")
            if result.returncode == 0:
                backup_info = self.parse_wbadmin_output(result.stdout)
                print(f"✓ Found {len(backup_info['versions'])} backup versions")
            else:
                print(f"⚠ wbadmin error: {result.stderr}")

        except Exception as e:
            print(f"✗ Error getting backup info: {e}")

        return backup_info

    def parse_wbadmin_output(self, output):
        """Parsea la salida de wbadmin get versions"""
        backup_info = {
            'versions': [],
            'last_backup': None,
            'backup_location': None,
            'status': 'unknown'
        }

        lines = output.split('\n')
        current_backup = None

        for line in lines:
            line = line.strip()

            # Buscar fecha de backup
            if 'Backup time:' in line:
                backup_time = line.replace('Backup time:', '').strip()
                current_backup = {'backup_time': backup_time}

            # Buscar ubicación de backup
            elif 'Backup location:' in line and current_backup:
                backup_location = line.replace('Backup location:', '').strip()
                current_backup['backup_location'] = backup_location

            # Buscar identificador de versión
            elif 'Version identifier:' in line and current_backup:
                version_id = line.replace('Version identifier:', '').strip()
                current_backup['version_identifier'] = version_id
                backup_info['versions'].append(current_backup)
                current_backup = None

        # Determinar último backup
        if backup_info['versions']:
            backup_info['last_backup'] = backup_info['versions'][0]['backup_time']
            backup_info['backup_location'] = backup_info['versions'][0]['backup_location']
            backup_info['status'] = 'found'

        return backup_info

    def get_office_info(self):
        """Obtiene información de licencias de Office"""
        office_info = {
            'installed': False,
            'version': None,
            'products': [],
            'activation_status': 'unknown'
        }

        try:
            # Intentar obtener información usando ospp.vbs
            # Buscar en ubicaciones comunes de Office
            office_paths = [
                r"C:\Program Files\Microsoft Office\Office16",
                r"C:\Program Files (x86)\Microsoft Office\Office16",
                r"C:\Program Files\Microsoft Office\Office15",
                r"C:\Program Files (x86)\Microsoft Office\Office15"
            ]
            print(f"🔍 Checking Office paths...")
            for path in office_paths:
                exists = os.path.exists(path)
                print(f"   {path}: {'✓' if exists else '✗'}")
                ospp_path = os.path.join(path, "ospp.vbs")
                if os.path.exists(ospp_path):
                    office_info['installed'] = True
                    office_info = self.get_office_license_info(ospp_path)
                    break

            if not office_info['installed']:
                print("ℹ No Office installation detected")
            else:
                print(f"✓ Office detected: {office_info.get('version', 'Unknown version')}")

        except Exception as e:
            print(f"✗ Error getting Office info: {e}")

        return office_info

    def get_office_license_info(self, ospp_path):
        """Obtiene detalles de licencia usando ospp.vbs"""
        office_info = {
            'installed': True,
            'version': None,
            'products': [],
            'activation_status': 'unknown'
        }

        try:
            # Ejecutar ospp.vbs /dstatus para obtener estado detallado
            result = subprocess.run(
                ['cscript', '//nologo', ospp_path, '/dstatus'],
                capture_output=True,
                text=True,
                shell=True,
                cwd=os.path.dirname(ospp_path)
            )

            if result.returncode == 0:
                office_info = self.parse_office_output(result.stdout)
            else:
                print(f"⚠ ospp.vbs error: {result.stderr}")

        except Exception as e:
            print(f"✗ Error running ospp.vbs: {e}")

        return office_info

    def parse_office_output(self, output):
        """Parsea la salida de ospp.vbs"""
        office_info = {
            'installed': True,
            'version': None,
            'products': [],
            'activation_status': 'unknown'
        }

        lines = output.split('\n')
        current_product = {}

        for line in lines:
            line = line.strip()

            if 'PRODUCT ID:' in line:
                if current_product:  # Guardar el producto anterior
                    office_info['products'].append(current_product)
                current_product = {}
                current_product['product_id'] = line.split(':', 1)[1].strip()

            elif 'LICENSE NAME:' in line and current_product:
                current_product['name'] = line.split(':', 1)[1].strip()

            elif 'LICENSE STATUS:' in line and current_product:
                status = line.split(':', 1)[1].strip()
                current_product['license_status'] = status

            elif 'Last 5 characters of installed product key:' in line and current_product:
                key = line.split(':', 1)[1].strip()
                current_product['partial_key'] = key

        # No olvides el último producto
        if current_product:
            office_info['products'].append(current_product)

        # Determinar estado general y versión
        if office_info['products']:
            activated_count = sum(1 for prod in office_info['products'] if 'LICENSED' in prod.get('license_status', ''))
            office_info['activation_status'] = f"{activated_count}/{len(office_info['products'])} activated"

            # Detectar versión basándose en los nombres
            if any('Office 19' in prod.get('name', '') for prod in office_info['products']):
                office_info['version'] = 'Office 2019'
            elif any('Office 16' in prod.get('name', '') for prod in office_info['products']):
                office_info['version'] = 'Office 2016/365'

        return office_info

    def get_cad_software_info(self):
        """Obtiene información de software CAD (SolidWorks, AutoCAD)"""
        cad_info = {
            'solidworks': {
                'installed': False,
                'version': None,
                'license_status': 'unknown',
                'expiration_date': None
            },
            'autocad': {
                'installed': False,
                'version': None,
                'license_status': 'unknown',
                'expiration_date': None
            }
        }

        try:
            # Detectar SolidWorks
            cad_info['solidworks'] = self.detect_solidworks()

            # Detectar AutoCAD
            cad_info['autocad'] = self.detect_autocad()

            installed_count = sum(1 for app in cad_info.values() if app['installed'])
            print(f"✓ CAD Software scan complete: {installed_count} applications found")

        except Exception as e:
            print(f"✗ Error getting CAD software info: {e}")

        return cad_info

    def detect_solidworks(self):
        """Detecta instalación y licencia de SolidWorks"""
        sw_info = {
            'installed': False,
            'version': None,
            'license_status': 'unknown',
            'expiration_date': None
        }

        try:
            import winreg

            # Buscar en el registro de Windows
            registry_paths = [
                r"SOFTWARE\SolidWorks",
                r"SOFTWARE\WOW6432Node\SolidWorks"
            ]

            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        sw_info['installed'] = True

                        # Buscar información de versión
                        try:
                            current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
                            sw_info['version'] = current_version
                        except FileNotFoundError:
                            pass

                        # Buscar información de licencia
                        try:
                            license_server, _ = winreg.QueryValueEx(key, "License Server")
                            sw_info['license_status'] = 'network_license' if license_server else 'standalone'
                        except FileNotFoundError:
                            sw_info['license_status'] = 'standalone'

                        print(f"✓ SolidWorks detected: {sw_info['version'] or 'Unknown version'}")
                        break

                except FileNotFoundError:
                    continue

        except Exception as e:
            print(f"⚠ Error detecting SolidWorks: {e}")

        return sw_info

    def detect_autocad(self):
        """Detecta instalación y licencia de AutoCAD"""
        autocad_info = {
            'installed': False,
            'version': None,
            'license_status': 'unknown',
            'expiration_date': None
        }

        try:
            import winreg

            # Buscar instalaciones de AutoCAD
            registry_paths = [
                r"SOFTWARE\Autodesk\AutoCAD",
                r"SOFTWARE\WOW6432Node\Autodesk\AutoCAD"
            ]

            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        # Enumerar versiones instaladas
                        i = 0
                        while True:
                            try:
                                version_key = winreg.EnumKey(key, i)
                                autocad_info['installed'] = True
                                autocad_info['version'] = version_key

                                # Intentar obtener más detalles
                                version_path = f"{reg_path}\\{version_key}"
                                try:
                                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, version_path) as version_reg:
                                        try:
                                            product_name, _ = winreg.QueryValueEx(version_reg, "ProductName")
                                            autocad_info['version'] = product_name
                                        except FileNotFoundError:
                                            pass
                                except FileNotFoundError:
                                    pass

                                i += 1

                            except OSError:
                                break

                        if autocad_info['installed']:
                            print(f"✓ AutoCAD detected: {autocad_info['version'] or 'Unknown version'}")
                            break

                except FileNotFoundError:
                    continue

            # Verificar licencias de Autodesk usando AdskLicensing
            if autocad_info['installed']:
                autocad_info['license_status'] = self.check_autodesk_licensing()

        except Exception as e:
            print(f"⚠ Error detecting AutoCAD: {e}")

        return autocad_info

    def check_autodesk_licensing(self):
        """Verifica el estado de las licencias de Autodesk"""
        try:
            # Intentar usar AdskLicensing command line tool
            autodesk_paths = [
                r"C:\Program Files (x86)\Common Files\Autodesk Shared\AdskLicensing",
                r"C:\Program Files\Common Files\Autodesk Shared\AdskLicensing"
            ]

            for path in autodesk_paths:
                licensing_tool = os.path.join(path, "AdskLicensingInstHelper.exe")
                if os.path.exists(licensing_tool):
                    try:
                        result = subprocess.run(
                            [licensing_tool, "list"],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if result.returncode == 0 and "ACTIVE" in result.stdout:
                            return "active"
                        elif result.returncode == 0:
                            return "installed_not_active"

                    except (subprocess.TimeoutExpired, FileNotFoundError):
                        pass

            # Si no encuentra la herramienta, asumir que está activo si está instalado
            return "assumed_active"

        except Exception as e:
            return "unknown"

    def register_with_server(self):
        try:
            system_info = self.get_system_info()
            response = requests.post(
                f"{self.server_url}/api/agents/register",
                json=system_info,
                timeout=10
            )

            if response.status_code == 200:
                print(f"✓ Agent registered successfully: {self.agent_id}")
                self.is_registered = True
                return True
            else:
                print(f"✗ Registration failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return False

    def send_monitoring_data(self):
        """Envía información completa de monitoreo al servidor"""
        try:
            # Obtener información de backups y Office
            backup_data = self.get_backup_info()
            office_data = self.get_office_info()
            cad_data = self.get_cad_software_info()

            payload = {
                'agent_id': self.agent_id,
                'backup_info': backup_data,
                'office_info': office_data,
                'cad_info': cad_data,
                'timestamp': datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.server_url}/api/agents/monitoring-data",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                print("✓ Monitoring data sent successfully")
                return True
            else:
                print(f"✗ Failed to send monitoring data: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Error sending monitoring data: {e}")
            return False

    def run(self):
        print("Starting Monitoring Agent...")
        print(f"Agent ID: {self.agent_id}")
        print(f"Server URL: {self.server_url}")

        if self.register_with_server():
            print("Agent registered. Getting backup information...")

            # Enviar datos de backup iniciales
            self.send_monitoring_data()

            print("Agent is running. Press Ctrl+C to stop.")

            try:
                while True:
                    time.sleep(60)  # Cada minuto
                    print("Checking and sending backup data...")
                    self.send_monitoring_data()

            except KeyboardInterrupt:
                print("\nStopping agent...")
        else:
            print("Failed to register with server. Exiting.")


if __name__ == "__main__":
    agent = MonitoringAgent()
    agent.run()