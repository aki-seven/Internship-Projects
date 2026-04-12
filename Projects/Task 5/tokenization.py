import sqlite3
import uuid
from typing import Optional

DB_PATH = 'tokens.db'

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            encrypted_pan TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def generate_token() -> str:
    """
    Generate a unique token.
    """
    return str(uuid.uuid4())

def store_token(encrypted_pan: str) -> str:
    """
    Store the encrypted PAN and return the token.
    """
    token = generate_token()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tokens (token, encrypted_pan) VALUES (?, ?)', (token, encrypted_pan))
    conn.commit()
    conn.close()
    return token

def get_encrypted_pan(token: str) -> Optional[str]:
    """
    Retrieve the encrypted PAN by token.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT encrypted_pan FROM tokens WHERE token = ?', (token,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# Initialize DB on import
init_db()
