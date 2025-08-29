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

    def get_agents_history(self) -> list[dict]:
        """Return aggregated monitoring data for all agents."""
        agents = Agent.query.all()
        results: list[dict] = []
        for agent in agents:
            office_record = (
                OfficeRecord.query.filter_by(agent_id=agent.agent_id)
                .order_by(OfficeRecord.recorded_at.desc())
                .first()
            )
            backup_record = (
                BackupRecord.query.filter_by(agent_id=agent.agent_id)
                .order_by(BackupRecord.recorded_at.desc())
                .first()
            )
            results.append(
                {
                    "agent_id": agent.agent_id,
                    "hostname": agent.hostname,
                    "ip_address": agent.ip_address,
                    "operating_system": agent.operating_system,
                    "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
                    "registered_at": agent.last_seen.isoformat() if agent.last_seen else None,
                    "office": self._office_to_dict(office_record),
                    "backup": self._backup_to_dict(backup_record),
                }
            )
        return results

    @staticmethod
    def _office_to_dict(record: OfficeRecord | None) -> dict | None:
        if not record:
            return None
        return {
            "installed": record.is_installed,
            "version": record.version,
            "activation_status": record.activation_status,
        }

    @staticmethod
    def _backup_to_dict(record: BackupRecord | None) -> dict | None:
        if not record:
            return None
        return {
            "status": record.backup_status,
            "location": record.backup_location,
            "last_backup": record.last_backup_date.isoformat() if record.last_backup_date else None,
        }
