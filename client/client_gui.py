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
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import pystray
from PIL import Image, ImageDraw
import sys


class MonitoringAgent:
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.agent_id = self.generate_agent_id()
        self.is_registered = False
        self.is_running = False
        self.monitoring_thread = None

        # Load configuration
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists('client_config.json'):
                with open('client_config.json', 'r') as f:
                    config = json.load(f)
                    self.server_url = config.get('server_url', 'http://localhost:5000')
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'server_url': self.server_url
            }
            with open('client_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

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
        """Get backup information using wbadmin"""
        backup_info = {
            'versions': [],
            'last_backup': None,
            'backup_location': None,
            'status': 'unknown'
        }

        try:
            result = subprocess.run(
                ['wbadmin', 'get', 'versions'],
                capture_output=True,
                text=True,
                shell=True,
                timeout=30
            )

            if result.returncode == 0:
                backup_info = self.parse_wbadmin_output(result.stdout)

        except Exception as e:
            print(f"Error getting backup info: {e}")

        return backup_info

    def parse_wbadmin_output(self, output):
        """Parse wbadmin get versions output"""
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

            if 'Backup time:' in line:
                backup_time = line.replace('Backup time:', '').strip()
                current_backup = {'backup_time': backup_time}

            elif 'Backup location:' in line and current_backup:
                backup_location = line.replace('Backup location:', '').strip()
                current_backup['backup_location'] = backup_location

            elif 'Version identifier:' in line and current_backup:
                version_id = line.replace('Version identifier:', '').strip()
                current_backup['version_identifier'] = version_id
                backup_info['versions'].append(current_backup)
                current_backup = None

        if backup_info['versions']:
            backup_info['last_backup'] = backup_info['versions'][0]['backup_time']
            backup_info['backup_location'] = backup_info['versions'][0]['backup_location']
            backup_info['status'] = 'found'

        return backup_info

    def get_office_info(self):
        """Get Office license information"""
        office_info = {
            'installed': False,
            'version': None,
            'products': [],
            'activation_status': 'unknown'
        }

        try:
            office_paths = [
                r"C:\Program Files\Microsoft Office\Office16",
                r"C:\Program Files (x86)\Microsoft Office\Office16",
                r"C:\Program Files\Microsoft Office\Office15",
                r"C:\Program Files (x86)\Microsoft Office\Office15"
            ]

            for path in office_paths:
                ospp_path = os.path.join(path, "ospp.vbs")
                if os.path.exists(ospp_path):
                    office_info['installed'] = True
                    office_info = self.get_office_license_info(ospp_path)
                    break

        except Exception as e:
            print(f"Error getting Office info: {e}")

        return office_info

    def get_office_license_info(self, ospp_path):
        """Get license details using ospp.vbs"""
        office_info = {
            'installed': True,
            'version': None,
            'products': [],
            'activation_status': 'unknown'
        }

        try:
            result = subprocess.run(
                ['cscript', '//nologo', ospp_path, '/dstatus'],
                capture_output=True,
                text=True,
                shell=True,
                cwd=os.path.dirname(ospp_path),
                timeout=30
            )

            if result.returncode == 0:
                office_info = self.parse_office_output(result.stdout)

        except Exception as e:
            print(f"Error running ospp.vbs: {e}")

        return office_info

    def parse_office_output(self, output):
        """Parse ospp.vbs output"""
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
                if current_product:
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

        if current_product:
            office_info['products'].append(current_product)

        if office_info['products']:
            activated_count = sum(1 for prod in office_info['products'] if 'LICENSED' in prod.get('license_status', ''))
            office_info['activation_status'] = f"{activated_count}/{len(office_info['products'])} activated"

            if any('Office 19' in prod.get('name', '') for prod in office_info['products']):
                office_info['version'] = 'Office 2019'
            elif any('Office 16' in prod.get('name', '') for prod in office_info['products']):
                office_info['version'] = 'Office 2016/365'

        return office_info

    def get_cad_software_info(self):
        """Get CAD software information (SolidWorks, AutoCAD)"""
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
            cad_info['solidworks'] = self.detect_solidworks()
            cad_info['autocad'] = self.detect_autocad()

        except Exception as e:
            print(f"Error getting CAD software info: {e}")

        return cad_info

    def detect_solidworks(self):
        """Detect SolidWorks installation and license"""
        sw_info = {
            'installed': False,
            'version': None,
            'license_status': 'unknown',
            'expiration_date': None
        }

        try:
            import winreg

            registry_paths = [
                r"SOFTWARE\SolidWorks",
                r"SOFTWARE\WOW6432Node\SolidWorks"
            ]

            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        sw_info['installed'] = True

                        try:
                            current_version, _ = winreg.QueryValueEx(key, "CurrentVersion")
                            sw_info['version'] = current_version
                        except FileNotFoundError:
                            pass

                        try:
                            license_server, _ = winreg.QueryValueEx(key, "License Server")
                            sw_info['license_status'] = 'network_license' if license_server else 'standalone'
                        except FileNotFoundError:
                            sw_info['license_status'] = 'standalone'

                        break

                except FileNotFoundError:
                    continue

        except Exception as e:
            print(f"Error detecting SolidWorks: {e}")

        return sw_info

    def detect_autocad(self):
        """Detect AutoCAD installation and license"""
        autocad_info = {
            'installed': False,
            'version': None,
            'license_status': 'unknown',
            'expiration_date': None
        }

        try:
            import winreg

            registry_paths = [
                r"SOFTWARE\Autodesk\AutoCAD",
                r"SOFTWARE\WOW6432Node\Autodesk\AutoCAD"
            ]

            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        i = 0
                        while True:
                            try:
                                version_key = winreg.EnumKey(key, i)
                                autocad_info['installed'] = True
                                autocad_info['version'] = version_key

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
                            autocad_info['license_status'] = self.check_autodesk_licensing()
                            break

                except FileNotFoundError:
                    continue

        except Exception as e:
            print(f"Error detecting AutoCAD: {e}")

        return autocad_info

    def check_autodesk_licensing(self):
        """Check Autodesk license status"""
        try:
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
                self.is_registered = True
                return True
            else:
                return False

        except requests.exceptions.RequestException as e:
            return False

    def send_monitoring_data(self):
        """Send complete monitoring information to server"""
        try:
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

            return response.status_code == 200

        except Exception as e:
            return False

    def monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                if not self.is_registered:
                    self.register_with_server()

                if self.is_registered:
                    self.send_monitoring_data()

                # Wait 60 seconds before next check
                for _ in range(60):
                    if not self.is_running:
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(60)

    def start_monitoring(self):
        """Start monitoring in separate thread"""
        if not self.is_running:
            self.is_running = True
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)


class SettingsWindow:
    def __init__(self, agent):
        self.agent = agent
        self.root = tk.Tk()
        self.root.title("Settings - Monitoring System")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        self.create_widgets()

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"500x400+{x}+{y}")

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        title_label = ttk.Label(main_frame, text="Client Configuration",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Agent information
        info_frame = ttk.LabelFrame(main_frame, text="Agent Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(info_frame, text="Agent ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=self.agent.agent_id, font=("Courier", 9)).grid(row=0, column=1, sticky=tk.W,
                                                                                  padx=(10, 0), pady=2)

        ttk.Label(info_frame, text="Hostname:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=socket.gethostname()).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # Server configuration
        server_frame = ttk.LabelFrame(main_frame, text="Server Configuration", padding="10")
        server_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(server_frame, text="Server URL:").grid(row=0, column=0, sticky=tk.W, pady=2)

        self.server_url_var = tk.StringVar(value=self.agent.server_url)
        server_entry = ttk.Entry(server_frame, textvariable=self.server_url_var, width=40)
        server_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 10))

        test_button = ttk.Button(server_frame, text="Test Connection",
                                 command=self.test_connection)
        test_button.grid(row=1, column=1, padx=(10, 0), pady=(5, 10))

        # Service status
        status_frame = ttk.LabelFrame(main_frame, text="Service Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))

        self.status_label = ttk.Label(status_frame, text="Status: Starting...",
                                      font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=2)

        self.connection_label = ttk.Label(status_frame, text="Connection: Checking...")
        self.connection_label.grid(row=1, column=0, sticky=tk.W, pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))

        save_button = ttk.Button(button_frame, text="Save", command=self.save_settings)
        save_button.grid(row=0, column=0, padx=(0, 10))

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.root.destroy)
        cancel_button.grid(row=0, column=1)

        # Update initial status
        self.update_status()

    def test_connection(self):
        """Test connection to server"""
        try:
            url = self.server_url_var.get().strip()
            if not url:
                messagebox.showerror("Error", "Please enter a valid URL")
                return

            response = requests.get(f"{url}/api/agents", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Connection successful")
            else:
                messagebox.showerror("Error", f"Connection error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Could not connect to server:\n{str(e)}")

    def save_settings(self):
        """Save settings"""
        url = self.server_url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        self.agent.server_url = url
        self.agent.save_config()
        self.agent.is_registered = False  # Force re-registration

        messagebox.showinfo("Saved", "Settings saved successfully")
        self.root.destroy()

    def update_status(self):
        """Update status displayed in window"""
        if self.agent.is_running:
            self.status_label.config(text="Status: ✓ Running", foreground="green")
        else:
            self.status_label.config(text="Status: ✗ Stopped", foreground="red")

        if self.agent.is_registered:
            self.connection_label.config(text="Connection: ✓ Connected", foreground="green")
        else:
            self.connection_label.config(text="Connection: ✗ Disconnected", foreground="red")

        # Schedule next update
        self.root.after(1000, self.update_status)

    def show(self):
        """Show window"""
        self.root.mainloop()


class MonitoringApp:
    def __init__(self):
        self.agent = MonitoringAgent()
        self.tray_icon = None

    def create_icon_image(self):
        """Create simple icon for system tray"""
        # Create simple 64x64 pixel image
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)

        # Draw blue circle
        draw.ellipse([8, 8, 56, 56], fill='#4CAF50', outline='#388E3C', width=2)

        # Draw "M" in center
        draw.text((24, 22), "M", fill='white', anchor="mm")

        return image

    def show_settings(self, icon, item):
        """Show settings window"""

        def run_settings():
            settings = SettingsWindow(self.agent)
            settings.show()

        # Run in separate thread to not block tray
        threading.Thread(target=run_settings, daemon=True).start()

    def quit_app(self, icon, item):
        """Close application"""
        self.agent.stop_monitoring()
        icon.stop()

    def setup_tray(self):
        """Setup system tray icon"""
        icon_image = self.create_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("Settings", self.show_settings),
            pystray.MenuItem("Exit", self.quit_app)
        )

        self.tray_icon = pystray.Icon(
            "monitoring_agent",
            icon_image,
            "Monitoring System",
            menu
        )

    def run(self):
        """Run application"""
        print("Starting Monitoring System...")

        # Start monitoring in background
        self.agent.start_monitoring()

        # Setup and show tray icon
        self.setup_tray()

        print("System started. Check system tray icon.")
        print("Right-click icon to access settings.")

        try:
            self.tray_icon.run()
        except KeyboardInterrupt:
            print("\nClosing application...")
            self.agent.stop_monitoring()


if __name__ == "__main__":
    # Check if running from packaged executable
    if getattr(sys, 'frozen', False):
        # If executable, hide console
        import ctypes

        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    app = MonitoringApp()
    app.run()