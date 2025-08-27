from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Agent(db.Model):
    __tablename__ = 'agents'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), unique=True, nullable=False)
    hostname = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    operating_system = db.Column(db.String(100), nullable=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relaciones
    office_records = db.relationship('OfficeRecord', backref='agent', lazy=True)
    cad_records = db.relationship('CadRecord', backref='agent', lazy=True)
    backup_records = db.relationship('BackupRecord', backref='agent', lazy=True)


class OfficeRecord(db.Model):
    __tablename__ = 'office_records'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agents.agent_id'), nullable=False)
    is_installed = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(100), nullable=True)
    activation_status = db.Column(db.String(100), nullable=True)
    products_data = db.Column(db.Text, nullable=True)  # JSON string
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class CadRecord(db.Model):
    __tablename__ = 'cad_records'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agents.agent_id'), nullable=False)
    software_name = db.Column(db.String(50), nullable=False)  # 'solidworks' or 'autocad'
    is_installed = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(100), nullable=True)
    license_status = db.Column(db.String(100), nullable=True)
    expiration_date = db.Column(db.DateTime, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class BackupRecord(db.Model):
    __tablename__ = 'backup_records'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(100), db.ForeignKey('agents.agent_id'), nullable=False)
    backup_location = db.Column(db.String(500), nullable=True)
    last_backup_date = db.Column(db.DateTime, nullable=True)
    backup_status = db.Column(db.String(50), nullable=True)
    versions_data = db.Column(db.Text, nullable=True)  # JSON string
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)