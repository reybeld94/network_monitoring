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
            db.session.commit()

        # Guardar datos de Office
        office_info = data.get('office_info', {})
        if office_info:
            office_record = OfficeRecord(
                agent_id=agent_id,
                is_installed=office_info.get('installed', False),
                version=office_info.get('version'),
                activation_status=office_info.get('activation_status'),
                products_data=json.dumps(office_info.get('products', []))
            )
            db.session.add(office_record)

        # Guardar datos de CAD
        cad_info = data.get('cad_info', {})
        if cad_info:
            # SolidWorks
            if 'solidworks' in cad_info:
                sw_info = cad_info['solidworks']
                cad_record = CadRecord(
                    agent_id=agent_id,
                    software_name='solidworks',
                    is_installed=sw_info.get('installed', False),
                    version=sw_info.get('version'),
                    license_status=sw_info.get('license_status'),
                    expiration_date=None  # Implementar después si es necesario
                )
                db.session.add(cad_record)

            # AutoCAD
            if 'autocad' in cad_info:
                ac_info = cad_info['autocad']
                cad_record = CadRecord(
                    agent_id=agent_id,
                    software_name='autocad',
                    is_installed=ac_info.get('installed', False),
                    version=ac_info.get('version'),
                    license_status=ac_info.get('license_status'),
                    expiration_date=None  # Implementar después si es necesario
                )
                db.session.add(cad_record)

        # Guardar datos de backup
        backup_info = data.get('backup_info', {})
        if backup_info:
            backup_record = BackupRecord(
                agent_id=agent_id,
                backup_location=backup_info.get('backup_location'),
                last_backup_date=None,  # Parsear después si hay fecha
                backup_status=backup_info.get('status'),
                versions_data=json.dumps(backup_info.get('versions', []))
            )
            db.session.add(backup_record)

        # Confirmar todos los cambios
        db.session.commit()

        print(f"📁 Received monitoring data from {agent_id}")
        print(f"   - Office: {'installed' if office_info.get('installed') else 'not detected'}")
        print(f"   - SolidWorks: {'installed' if cad_info.get('solidworks', {}).get('installed') else 'not detected'}")
        print(f"   - AutoCAD: {'installed' if cad_info.get('autocad', {}).get('installed') else 'not detected'}")

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

if __name__ == '__main__':
    print("Starting Monitoring System Server...")
    print("Available endpoints:")
    print("  - http://localhost:5000 (home)")
    print("  - http://localhost:5000/api/agents (list agents)")
    print("  - http://localhost:5000/api/backups (all backup data)")
    app.run(debug=True, host='0.0.0.0', port=5000)