"""Flask application entry point for the monitoring server."""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask

# When this file is executed directly (e.g. ``python server/app.py``) the
# package context is not set, causing relative imports to fail. To support both
# direct execution and package imports we ensure the repository root is on the
# module search path and then use absolute imports.
if __package__ is None or __package__ == "":  # pragma: no cover - runtime convenience
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from server.config.server_config import ServerConfig
from server.models import db
from server.api.agents import agents_bp
from server.api.hardware import hardware_bp
from server.api.software import software_bp
from server.api.statistics import statistics_bp
from server.api.search import search_bp


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
    app.register_blueprint(search_bp)
    return app


if __name__ == '__main__':  # pragma: no cover - script entry
    create_app().run(debug=True)
