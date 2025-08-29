from datetime import datetime
from ..models import db, Agent


class AgentService:
    """Business logic related to agents."""

    def register_agent(self, data, ip_address: str) -> Agent:
        agent = Agent.query.filter_by(agent_id=data['agent_id']).first()
        if not agent:
            agent = Agent(agent_id=data['agent_id'])
            db.session.add(agent)
        agent.hostname = data.get('hostname')
        agent.ip_address = ip_address
        agent.operating_system = data.get('os')
        agent.last_seen = datetime.utcnow()
        agent.service_tag = data.get('service_tag')
        agent.serial_number = data.get('serial_number')
        agent.manufacturer = data.get('manufacturer')
        agent.model = data.get('model')
        agent.detection_method = data.get('detection_method')
        db.session.commit()
        return agent

    def get_by_service_tag(self, service_tag: str) -> Agent | None:
        return Agent.query.filter_by(service_tag=service_tag).first()

    def search(self, query: str) -> list[Agent]:
        pattern = f"%{query.replace('*', '%')}%"
        return Agent.query.filter(
            db.or_(
                Agent.hostname.ilike(pattern),
                Agent.service_tag.ilike(pattern),
                Agent.serial_number.ilike(pattern),
                Agent.model.ilike(pattern),
            )
        ).all()
