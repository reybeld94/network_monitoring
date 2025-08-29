"""Simple database migration to add service tag columns."""

import sqlite3
from .config.server_config import ServerConfig


COLUMNS = {
    "service_tag": "VARCHAR(50)",
    "serial_number": "VARCHAR(50)",
    "manufacturer": "VARCHAR(100)",
    "model": "VARCHAR(100)",
    "detection_method": "VARCHAR(50)",
}


def migrate_database() -> None:
    cfg = ServerConfig()
    db_path = cfg.database_uri.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(agent)")
    existing = {row[1] for row in cur.fetchall()}
    for column, col_type in COLUMNS.items():
        if column not in existing:
            cur.execute(f"ALTER TABLE agent ADD COLUMN {column} {col_type}")
            print(f"Added column {column}")
    conn.commit()
    conn.close()


if __name__ == "__main__":  # pragma: no cover - script entry
    migrate_database()
