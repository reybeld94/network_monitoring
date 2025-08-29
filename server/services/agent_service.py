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
        db.session.commit()
        return agent
