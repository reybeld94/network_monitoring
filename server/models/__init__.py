from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from .agent import Agent  # noqa: E402
from .software import OfficeRecord, CadRecord  # noqa: E402
from .backup import BackupRecord  # noqa: E402

__all__ = ["db", "Agent", "OfficeRecord", "CadRecord", "BackupRecord"]
