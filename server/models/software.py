from datetime import datetime
from . import db


class OfficeRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(120), db.ForeignKey('agent.agent_id'))
    is_installed = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(50))
    activation_status = db.Column(db.String(50))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)


class CadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(120), db.ForeignKey('agent.agent_id'))
    software_name = db.Column(db.String(50))
    is_installed = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(50))
    license_status = db.Column(db.String(50))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
