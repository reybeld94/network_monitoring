from flask import Flask, request, jsonify, render_template
from datetime import datetime
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

        # Manejar datos de Office - ACTUALIZAR en lugar de insertar
        office_info = data.get('office_info', {})
        if office_info:
            existing_office = OfficeRecord.query.filter_by(agent_id=agent_id).order_by(
                OfficeRecord.recorded_at.desc()).first()

            # Solo crear nuevo registro si hay cambios significativos
            should_create_new = False
            if not existing_office:
                should_create_new = True
            else:
                # Verificar si hay cambios
                if (existing_office.is_installed != office_info.get('installed', False) or
                        existing_office.version != office_info.get('version') or
                        existing_office.activation_status != office_info.get('activation_status') or
                        json.dumps(existing_office.products_data or []) != json.dumps(office_info.get('products', []))):
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
                # Actualizar timestamp del registro existente
                existing_office.recorded_at = datetime.utcnow()
                print(f"📄 Office record updated (timestamp) for {agent_id}")

        # Manejar datos de CAD - ACTUALIZAR en lugar de insertar
        cad_info = data.get('cad_info', {})
        if cad_info:
            # SolidWorks
            if 'solidworks' in cad_info:
                sw_info = cad_info['solidworks']
                existing_sw = CadRecord.query.filter_by(agent_id=agent_id, software_name='solidworks').order_by(
                    CadRecord.recorded_at.desc()).first()

                should_create_new = False
                if not existing_sw:
                    should_create_new = True
                else:
                    if (existing_sw.is_installed != sw_info.get('installed', False) or
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
                else:
                    existing_sw.recorded_at = datetime.utcnow()

            # AutoCAD
            if 'autocad' in cad_info:
                ac_info = cad_info['autocad']
                existing_ac = CadRecord.query.filter_by(agent_id=agent_id, software_name='autocad').order_by(
                    CadRecord.recorded_at.desc()).first()

                should_create_new = False
                if not existing_ac:
                    should_create_new = True
                else:
                    if (existing_ac.is_installed != ac_info.get('installed', False) or
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
                else:
                    existing_ac.recorded_at = datetime.utcnow()

        # Manejar datos de backup - ACTUALIZAR en lugar de insertar
        backup_info = data.get('backup_info', {})
        if backup_info:
            existing_backup = BackupRecord.query.filter_by(agent_id=agent_id).order_by(
                BackupRecord.recorded_at.desc()).first()

            should_create_new = False
            if not existing_backup:
                should_create_new = True
            else:
                if (existing_backup.backup_location != backup_info.get('backup_location') or
                        existing_backup.backup_status != backup_info.get('status') or
                        json.dumps(existing_backup.versions_data or []) != json.dumps(backup_info.get('versions', []))):
                    should_create_new = True

            if should_create_new:
                backup_record = BackupRecord(
                    agent_id=agent_id,
                    backup_location=backup_info.get('backup_location'),
                    last_backup_date=None,
                    backup_status=backup_info.get('status'),
                    versions_data=json.dumps(backup_info.get('versions', []))
                )
                db.session.add(backup_record)
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
    return jsonify({
        'monitoring_data': monitoring_data,
        'total': len(monitoring_data)
    })


@app.route('/api/agents/<agent_id>/backups', methods=['GET'])
def get_agent_backups(agent_id):
    if agent_id in monitoring_data:
        return jsonify(monitoring_data[agent_id])
    else:
        return jsonify({'error': 'No backup data found for agent'}), 404

@app.route('/')
def home():
    return jsonify({
        'message': 'Monitoring System Server',
        'status': 'running',
        'dashboard': 'http://localhost:5000/dashboard',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/agents/history')
def agents_history():
    """Obtiene historial completo de todos los agentes"""
    agents_list = Agent.query.all()

    result = []
    for agent in agents_list:
        # Obtener último registro de cada tipo
        latest_office = OfficeRecord.query.filter_by(agent_id=agent.agent_id).order_by(
            OfficeRecord.recorded_at.desc()).first()
        latest_backup = BackupRecord.query.filter_by(agent_id=agent.agent_id).order_by(
            BackupRecord.recorded_at.desc()).first()

        # CAD records
        latest_solidworks = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='solidworks').order_by(
            CadRecord.recorded_at.desc()).first()
        latest_autocad = CadRecord.query.filter_by(agent_id=agent.agent_id, software_name='autocad').order_by(
            CadRecord.recorded_at.desc()).first()

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
            } if latest_office else None,
            'solidworks': {
                'installed': latest_solidworks.is_installed if latest_solidworks else False,
                'version': latest_solidworks.version if latest_solidworks else None,
                'license_status': latest_solidworks.license_status if latest_solidworks else None
            } if latest_solidworks else None,
            'autocad': {
                'installed': latest_autocad.is_installed if latest_autocad else False,
                'version': latest_autocad.version if latest_autocad else None,
                'license_status': latest_autocad.license_status if latest_autocad else None
            } if latest_autocad else None,
            'backup': {
                'location': latest_backup.backup_location if latest_backup else None,
                'status': latest_backup.backup_status if latest_backup else None,
                'last_backup': latest_backup.last_backup_date.isoformat() if latest_backup and latest_backup.last_backup_date else None
            } if latest_backup else None
        }
        result.append(agent_data)

    return jsonify({
        'agents': result,
        'total': len(result)
    })


@app.route('/api/statistics')
def get_statistics():
    """Obtiene estadísticas generales del sistema usando solo los registros más recientes"""
    total_agents = Agent.query.count()
    active_agents = Agent.query.filter_by(is_active=True).count()

    # Contar software instalado usando solo el registro más reciente de cada agente
    office_installs = 0
    solidworks_installs = 0
    autocad_installs = 0
    active_backups = 0

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

        # Backups - solo el último registro
        latest_backup = BackupRecord.query.filter_by(agent_id=agent.agent_id).order_by(
            BackupRecord.recorded_at.desc()).first()
        if latest_backup and latest_backup.backup_status != 'unknown':
            active_backups += 1

    return jsonify({
        'total_agents': total_agents,
        'active_agents': active_agents,
        'office_installs': office_installs,
        'cad_installs': solidworks_installs + autocad_installs,
        'active_backups': active_backups,
        'software_breakdown': {
            'office': office_installs,
            'solidworks': solidworks_installs,
            'autocad': autocad_installs
        }
    })

if __name__ == '__main__':
    print("Starting Monitoring System Server...")
    print("Available endpoints:")
    print("  - http://localhost:5000 (home)")
    print("  - http://localhost:5000/api/agents (list agents)")
    print("  - http://localhost:5000/api/backups (all backup data)")
    app.run(debug=True, host='0.0.0.0', port=5000)