from flask import Flask
from .config.server_config import ServerConfig
from .models import db
from .api.agents import agents_bp
from .api.hardware import hardware_bp
from .api.software import software_bp
from .api.statistics import statistics_bp


def create_app(config: ServerConfig | None = None) -> Flask:
    """Application factory for the monitoring server."""
    app = Flask(__name__)
    cfg = config or ServerConfig()
    app.config['SQLALCHEMY_DATABASE_URI'] = cfg.database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(agents_bp)
    app.register_blueprint(hardware_bp)
    app.register_blueprint(software_bp)
    app.register_blueprint(statistics_bp)
    return app


if __name__ == '__main__':  # pragma: no cover - script entry
    create_app().run(debug=True)
