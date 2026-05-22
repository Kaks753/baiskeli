"""
init_db.py — Creates tables from schema.sql and seeds default users.

Called once at startup from app.py.  Safe to run multiple times
(all CREATE TABLE statements use IF NOT EXISTS).
"""

import sqlite3
import os
import bcrypt

from db_config import DB_PATH


def init_db():
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

    conn = sqlite3.connect(DB_PATH)

    with open(schema_path, "r") as f:
        conn.executescript(f.read())

    _seed_default_users(conn)

    conn.commit()
    conn.close()
    print(f"✅ Database ready at: {DB_PATH}")


def _seed_default_users(conn):
    """Insert admin + cashier if they don't already exist."""
    cursor = conn.cursor()

    defaults = [
        ("admin",   "admin2026",   "admin"),
        ("cashier", "cashier2026", "cashier"),
    ]

    for username, password, role in defaults:
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed, role),
            )
            print(f"  ✅ Default user created: {username} ({role})")


if __name__ == "__main__":
    init_db()
