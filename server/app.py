from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
import json
import os
from models import db, Agent, OfficeRecord, CadRecord, BackupRecord

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db.init_app(app)

# Crear las tablas
with app.app_context():
    db.create_all()
    print("✓ Database initialized successfully")

# Almacenamiento temporal (mantenemos por compatibilidad)
agents = {}
monitoring_data = {}


# Utility functions
def parse_backup_versions(versions_data_str):
    """Parse backup versions from JSON string"""
    if not versions_data_str:
        return []
    try:
        return json.loads(versions_data_str)
    except json.JSONDecodeError:
        return []


def get_backup_summary(agent_id):
    """Get comprehensive backup summary for an agent"""
    try:
        backup_record = BackupRecord.query.filter_by(agent_id=agent_id).order_by(
            BackupRecord.recorded_at.desc()).first()

        if not backup_record:
            return {
                'status': 'none',
                'location': None,
                'last_backup': None,
                'versions_count': 0,
                'versions': []
            }

        versions = parse_backup_versions(backup_record.versions_data)

        # Try to parse last backup date from versions
        last_backup_date = backup_record.last_backup_date
        if not last_backup_date and versions:
            # Try to extract date from first version
            try:
                if isinstance(versions, list) and len(versions) > 0:
                    first_version = versions[0]
                    if isinstance(first_version, dict) and 'backup_time' in first_version:
                        backup_time_str = first_version['backup_time']
                        for fmt in ['%m/%d/%Y %I:%M %p', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                            try:
                                last_backup_date = datetime.strptime(backup_time_str, fmt)
                                break
                            except ValueError:
                                continue
            except (ValueError, KeyError, IndexError, TypeError):
                pass

        return {
            'status': backup_record.backup_status or 'unknown',
            'location': backup_record.backup_location,
            'last_backup': last_backup_date.isoformat() if last_backup_date else None,
            'versions_count': len(versions) if versions else 0,
            'versions': versions or []
        }
    except Exception as e:
        print(f"Error getting backup summary for {agent_id}: {e}")
        return {
            'status': 'error',
            'location': None,
            'last_backup': None,
            'versions_count': 0,
            'versions': []
        }


@app.route('/api/agents/register', methods=['POST'])
def register_agent():
    data = request.get_json()

    if not data or 'agent_id' not in data:
        return jsonify({'error': 'agent_id is required'}), 400

    agent_id = data['agent_id']

    # Buscar si el agente ya existe
    existing_agent = Agent.query.filter_by(agent_id=agent_id).first()

    if existing_agent:
        # Actualizar agente existente
        existing_agent.hostname = data.get('hostname', 'unknown')
        existing_agent.ip_address = request.remote_addr
        existing_agent.operating_system = data.get('os', 'unknown')
        existing_agent.last_seen = datetime.utcnow()
        existing_agent.is_active = True
        print(f"✓ Updated existing agent: {agent_id}")
    else:
        # Crear nuevo agente
        new_agent = Agent(
            agent_id=agent_id,
            hostname=data.get('hostname', 'unknown'),
            ip_address=request.remote_addr,
            operating_system=data.get('os', 'unknown')
        )
        db.session.add(new_agent)
        print(f"✓ Registered new agent: {agent_id}")

    db.session.commit()

    # Mantener compatibilidad con el sistema anterior
    agents[agent_id] = {
        'agent_id': agent_id,
        'hostname': data.get('hostname', 'unknown'),
        'ip': request.remote_addr,
        'os': data.get('os', 'unknown'),
        'last_seen': datetime.now().isoformat(),
        'registered_at': datetime.now().isoformat()
    }

    return jsonify({
        'message': 'Agent registered successfully',
        'agent_id': agent_id
    })


@app.route('/api/agents/monitoring-data', methods=['POST'])
def receive_monitoring_data():
    data = request.get_json()

    if not data or 'agent_id' not in data:
        return jsonify({'error': 'agent_id is required'}), 400

    agent_id = data['agent_id']

    try:
        # Actualizar última vez visto del agente
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if agent:
            agent.last_seen = datetime.utcnow()

        # Manejar datos de Office - ACTUALIZAR en lugar de insertar duplicados
        office_info = data.get('office_info', {})
        if office_info:
            existing_office = OfficeRecord.query.filter_by(agent_id=agent_id).order_by(
                OfficeRecord.recorded_at.desc()).first()

            should_create_new = False
            if not existing_office:
                should_create_new = True
            else:
                # Verificar si hay cambios significativos
                if (existing_office.is_installed != office_info.get('installed', False) or
                        existing_office.version != office_info.get('version') or
                        existing_office.activation_status != office_info.get('activation_status')):
                    should_create_new = True

            if should_create_new:
                office_record = OfficeRecord(
                    agent_id=agent_id,
                    is_installed=office_info.get('installed', False),
                    version=office_info.get('version'),
                    activation_status=office_info.get('activation_status'),
                    products_data=json.dumps(office_info.get('products', []))
                )
                db.session.add(office_record)
                print(f"📄 New Office record created for {agent_id}")
            else:
                existing_office.recorded_at = datetime.utcnow()

        # Manejar datos de CAD
        cad_info = data.get('cad_info', {})
        if cad_info:
            # SolidWorks
            if 'solidworks' in cad_info:
                sw_info = cad_info['solidworks']
                existing_sw = CadRecord.query.filter_by(agent_id=agent_id, software_name='solidworks').order_by(
                    CadRecord.recorded_at.desc()).first()

                should_create_new = False
                if not existing_sw or (existing_sw.is_installed != sw_info.get('installed', False) or
                                       existing_sw.version != sw_info.get('version') or
                                       existing_sw.license_status != sw_info.get('license_status')):
                    should_create_new = True

                if should_create_new:
                    cad_record = CadRecord(
                        agent_id=agent_id,
                        software_name='solidworks',
                        is_installed=sw_info.get('installed', False),
                        version=sw_info.get('version'),
                        license_status=sw_info.get('license_status'),
                        expiration_date=None
                    )
                    db.session.add(cad_record)

            # AutoCAD
            if 'autocad' in cad_info:
                ac_info = cad_info['autocad']
                existing_ac = CadRecord.query.filter_by(agent_id=agent_id, software_name='autocad').order_by(
                    CadRecord.recorded_at.desc()).first()

                should_create_new = False
                if not existing_ac or (existing_ac.is_installed != ac_info.get('installed', False) or
                                       existing_ac.version != ac_info.get('version') or
                                       existing_ac.license_status != ac_info.get('license_status')):
                    should_create_new = True

                if should_create_new:
                    cad_record = CadRecord(
                        agent_id=agent_id,
                        software_name='autocad',
                        is_installed=ac_info.get('installed', False),
                        version=ac_info.get('version'),
                        license_status=ac_info.get('license_status'),
                        expiration_date=None
                    )
                    db.session.add(cad_record)

        # Manejar datos de backup con mejor parsing
        backup_info = data.get('backup_info', {})
        if backup_info:
            existing_backup = BackupRecord.query.filter_by(agent_id=agent_id).order_by(
                BackupRecord.recorded_at.desc()).first()

            should_create_new = False
            if not existing_backup:
                should_create_new = True
            else:
                # Check for changes in backup data
                existing_versions = parse_backup_versions(existing_backup.versions_data)
                new_versions = backup_info.get('versions', [])

                if (existing_backup.backup_location != backup_info.get('backup_location') or
                        existing_backup.backup_status != backup_info.get('status') or
                        len(existing_versions) != len(new_versions)):
                    should_create_new = True

            if should_create_new:
                # Try to parse last backup date from versions
                last_backup_date = None
                versions = backup_info.get('versions', [])
                if versions and isinstance(versions, list) and len(versions) > 0:
                    try:
                        if isinstance(versions[0], dict) and 'backup_time' in versions[0]:
                            backup_time_str = versions[0]['backup_time']
                            # Try different date formats
                            for fmt in ['%m/%d/%Y %I:%M %p', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                                try:
                                    last_backup_date = datetime.strptime(backup_time_str, fmt)
                                    break
                                except ValueError:
                                    continue
                    except (KeyError, TypeError, AttributeError):
                        pass

                backup_record = BackupRecord(
                    agent_id=agent_id,
                    backup_location=backup_info.get('backup_location'),
                    last_backup_date=last_backup_date,
                    backup_status=backup_info.get('status', 'unknown'),
                    versions_data=json.dumps(backup_info.get('versions', []))
                )
                db.session.add(backup_record)
                print(f"💾 New backup record created for {agent_id}")
            else:
                existing_backup.recorded_at = datetime.utcnow()

        # Confirmar todos los cambios
        db.session.commit()

        print(f"📁 Processed monitoring data from {agent_id}")

        # Mantener compatibilidad con el sistema anterior
        monitoring_data[agent_id] = {
            'agent_id': agent_id,
            'backup_info': data.get('backup_info', {}),
            'office_info': data.get('office_info', {}),
            'cad_info': data.get('cad_info', {}),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'received_at': datetime.now().isoformat()
        }

        return jsonify({
            'message': 'Monitoring data received successfully',
            'agent_id': agent_id
        })

    except Exception as e:
        db.session.rollback()
        print(f"✗ Error saving monitoring data: {e}")
        return jsonify({'error': 'Failed to save monitoring data'}), 500


@app.route('/api/agents', methods=['GET'])
def list_agents():
    return jsonify({
        'agents': list(agents.values()),
        'total': len(agents)
    })


@app.route('/api/backups', methods=['GET'])
def list_backups():
    """Enhanced backup listing with detailed information"""
    try:
        # Get all agents with their latest backup info
        agents_list = Agent.query.all()
        backup_data = []

        for agent in agents_list:
            backup_summary = get_backup_summary(agent.agent_id)

            backup_data.append({
                'agent_id': agent.agent_id,
                'hostname': agent.hostname,
                'ip_address': agent.ip_address,
                'operating_system': agent.operating_system,
                'last_seen': agent.last_seen.isoformat() if agent.last_seen else None,
                'backup_info': backup_summary
            })

        return jsonify({
            'backups': backup_data,
            'total': len(backup_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/<agent_id>/backups', methods=['GET'])
def get_agent_backups(agent_id):
    """Get backup information for a specific agent"""
    try:
        backup_summary = get_backup_summary(agent_id)
        if backup_summary['status'] != 'none':
            return jsonify(backup_summary)
        else:
            return jsonify({'error': 'No backup data found for agent'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/<agent_id>/backup-history', methods=['GET'])
def get_agent_backup_history(agent_id):
    """Get complete backup history for an agent"""
    try:
        records = BackupRecord.query.filter_by(agent_id=agent_id).order_by(
            BackupRecord.recorded_at.desc()).all()

        history = []
        for record in records:
            versions = parse_backup_versions(record.versions_data)
            history.append({
                'recorded_at': record.recorded_at.isoformat(),
                'backup_location': record.backup_location,
                'backup_status': record.backup_status,
                'last_backup_date': record.last_backup_date.isoformat() if record.last_backup_date else None,
                'versions_count': len(versions),
                'versions': versions
            })

        return jsonify({
            'agent_id': agent_id,
            'history': history,
            'total_records': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def home():
    return jsonify({
        'message': 'Monitoring System Server',
        'status': 'running',
        'dashboard': f'http://localhost:7446/dashboard',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/agents/history')
def agents_history():
    """Obtiene historial completo de todos los agentes con información mejorada de backups"""
    agents_list = Agent.query.all()

    result = []
    for agent in agents_list:
        # Obtener último registro de cada tipo
        latest_office = OfficeRecord.query.filter_by(agent_id=agent.agent_id).order_by(
            OfficeRecord.recorded_at.desc()).first()

        # CAD records
        latest_solidworks = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='solidworks').order_by(
            CadRecord.recorded_at.desc()).first()
        latest_autocad = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='autocad').order_by(
            CadRecord.recorded_at.desc()).first()

        # Backup information with enhanced details
        backup_summary = get_backup_summary(agent.agent_id)

        agent_data = {
            'agent_id': agent.agent_id,
            'hostname': agent.hostname,
            'ip_address': agent.ip_address,
            'operating_system': agent.operating_system,
            'registered_at': agent.registered_at.isoformat() if agent.registered_at else None,
            'last_seen': agent.last_seen.isoformat() if agent.last_seen else None,
            'is_active': agent.is_active,
            'office': {
                'installed': latest_office.is_installed if latest_office else False,
                'version': latest_office.version if latest_office else None,
                'activation_status': latest_office.activation_status if latest_office else None,
                'products': json.loads(
                    latest_office.products_data) if latest_office and latest_office.products_data else []
            } if latest_office else {'installed': False},
            'solidworks': {
                'installed': latest_solidworks.is_installed if latest_solidworks else False,
                'version': latest_solidworks.version if latest_solidworks else None,
                'license_status': latest_solidworks.license_status if latest_solidworks else None
            } if latest_solidworks else {'installed': False},
            'autocad': {
                'installed': latest_autocad.is_installed if latest_autocad else False,
                'version': latest_autocad.version if latest_autocad else None,
                'license_status': latest_autocad.license_status if latest_autocad else None
            } if latest_autocad else {'installed': False},
            'backup': backup_summary
        }
        result.append(agent_data)

    return jsonify({
        'agents': result,
        'total': len(result)
    })


@app.route('/api/statistics')
def get_statistics():
    """Obtiene estadísticas generales del sistema con mejor conteo de backups"""
    total_agents = Agent.query.count()

    # Calcular agentes activos (última conexión en las últimas 24 horas)
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    active_agents = Agent.query.filter(Agent.last_seen > cutoff_time).count()

    # Contar software instalado usando solo el registro más reciente de cada agente
    office_installs = 0
    solidworks_installs = 0
    autocad_installs = 0
    active_backups = 0
    backup_with_recent_activity = 0

    # Obtener todos los agentes únicos
    agents = Agent.query.all()

    for agent in agents:
        # Office - solo el último registro
        latest_office = OfficeRecord.query.filter_by(agent_id=agent.agent_id).order_by(
            OfficeRecord.recorded_at.desc()).first()
        if latest_office and latest_office.is_installed:
            office_installs += 1

        # SolidWorks - solo el último registro
        latest_sw = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='solidworks').order_by(
            CadRecord.recorded_at.desc()).first()
        if latest_sw and latest_sw.is_installed:
            solidworks_installs += 1

        # AutoCAD - solo el último registro
        latest_ac = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='autocad').order_by(
            CadRecord.recorded_at.desc()).first()
        if latest_ac and latest_ac.is_installed:
            autocad_installs += 1

        # Backups - conteo mejorado
        backup_summary = get_backup_summary(agent.agent_id)
        if backup_summary['status'] == 'found':
            active_backups += 1

            # Check if backup is recent (within last week)
            if backup_summary['last_backup']:
                try:
                    # Handle both ISO format with and without timezone
                    last_backup_str = backup_summary['last_backup']
                    if last_backup_str.endswith('Z'):
                        last_backup_str = last_backup_str[:-1] + '+00:00'
                    elif '+' not in last_backup_str and 'T' in last_backup_str:
                        # Assume UTC if no timezone info
                        pass

                    last_backup = datetime.fromisoformat(last_backup_str.replace('Z', ''))
                    week_ago = datetime.utcnow() - timedelta(days=7)

                    # Compare without timezone info for simplicity
                    if last_backup.replace(tzinfo=None) > week_ago:
                        backup_with_recent_activity += 1
                except (ValueError, AttributeError) as e:
                    print(f"Error parsing backup date for agent {agent.agent_id}: {e}")

    return jsonify({
        'total_agents': total_agents,
        'active_agents': active_agents,
        'office_installs': office_installs,
        'cad_installs': solidworks_installs + autocad_installs,
        'active_backups': active_backups,
        'recent_backups': backup_with_recent_activity,
        'software_breakdown': {
            'office': office_installs,
            'solidworks': solidworks_installs,
            'autocad': autocad_installs
        },
        'backup_breakdown': {
            'total_configured': active_backups,
            'recent_activity': backup_with_recent_activity,
            'inactive': total_agents - active_backups
        }
    })


if __name__ == '__main__':
    print("Starting Enhanced Monitoring System Server...")
    print("Available endpoints:")
    print("  - http://localhost:7446 (home)")
    print("  - http://localhost:7446/dashboard (enhanced dashboard)")
    print("  - http://localhost:7446/api/agents (list agents)")
    print("  - http://localhost:7446/api/backups (enhanced backup data)")
    print("  - http://localhost:7446/api/statistics (enhanced statistics)")
    print("  - http://localhost:7446/api/agents/<id>/backup-history (backup history)")
    app.run(debug=True, host='0.0.0.0', port=7446)