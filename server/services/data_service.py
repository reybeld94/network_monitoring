from datetime import datetime
from ..models import db, Agent, OfficeRecord, CadRecord, BackupRecord


class DataService:
    """Persist monitoring data received from agents."""

    def store_monitoring_data(self, agent_id: str, payload: dict) -> None:
        agent = Agent.query.filter_by(agent_id=agent_id).first()
        if not agent:
            return
        agent.last_seen = datetime.utcnow()
        office = payload.get('software', {}).get('office', {})
        if office:
            record = OfficeRecord(
                agent_id=agent_id,
                is_installed=office.get('installed', False),
                version=office.get('version'),
                activation_status=office.get('activation_status'),
            )
            db.session.add(record)
        backup = payload.get('backup', {})
        if backup:
            record = BackupRecord(
                agent_id=agent_id,
                backup_status=backup.get('status'),
                backup_location=backup.get('backup_location'),
                versions_data=backup.get('output'),
            )
            db.session.add(record)
        db.session.commit()
