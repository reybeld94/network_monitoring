from datetime import datetime
from . import db


class BackupRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(120), db.ForeignKey('agent.agent_id'))
    backup_status = db.Column(db.String(50))
    backup_location = db.Column(db.String(255))
    versions_data = db.Column(db.Text)
    last_backup_date = db.Column(db.DateTime)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
