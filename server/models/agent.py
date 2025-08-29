from datetime import datetime
from . import db


class Agent(db.Model):
    """Registered monitoring agent."""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.String(120), unique=True, nullable=False)
    hostname = db.Column(db.String(120))
    ip_address = db.Column(db.String(45))
    operating_system = db.Column(db.String(120))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
