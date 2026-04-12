import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS pan_tokens (
    token TEXT PRIMARY KEY,
    encrypted_pan TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class TokenStorage:
    """SQLite backed storage for token -> encrypted PAN mappings."""

    def __init__(self, db_path: str):
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_file), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def close(self) -> None:
        """Close the database connection to release file locks."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "TokenStorage":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _create_table(self) -> None:
        self.conn.execute(CREATE_TABLE_SQL)
        self.conn.commit()

    def save_token(self, token: str, encrypted_pan: str) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.conn.execute(
            "INSERT INTO pan_tokens (token, encrypted_pan, created_at) VALUES (?, ?, ?)",
            (token, encrypted_pan, now),
        )
        self.conn.commit()

    def get_encrypted_pan(self, token: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT encrypted_pan FROM pan_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        return row["encrypted_pan"] if row else None
