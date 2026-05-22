

# # --- Initialize default users on module load ---
# create_users_table()
# initialize_users()

"""
auth.py — Authentication with bcrypt, rate limiting, audit logging.
"""
import sqlite3
import bcrypt
import time
from datetime import datetime

DB_NAME = "Databases/baiskeli.db"

# In-memory brute-force protection: {username: [timestamp, ...]}
_failed_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_users_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def initialize_users():
    conn = get_connection()
    cursor = conn.cursor()

    defaults = [
        ("admin", "admin2026", "admin"),
        ("cashier", "cashier2026", "cashier"),
    ]

    for username, password, role in defaults:
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        if not cursor.fetchone():
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed, role)
            )

    conn.commit()
    conn.close()

def _is_locked_out(username):
    attempts = _failed_attempts.get(username, [])
    now = time.time()
    recent = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _failed_attempts[username] = recent
    return len(recent) >= MAX_ATTEMPTS

def _record_failure(username):
    _failed_attempts.setdefault(username, []).append(time.time())

def _clear_failures(username):
    _failed_attempts.pop(username, None)

def login(username, password):
    if _is_locked_out(username):
        remaining = int(LOCKOUT_SECONDS - (time.time() - min(_failed_attempts[username])))
        raise Exception(f"Account locked. Try again in {remaining//60}m {remaining%60}s.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password, role, is_active FROM users WHERE username=?", (username,)
    )
    row = cursor.fetchone()

    if row:
        stored_hash, role, is_active = row
        if not is_active:
            conn.close()
            raise Exception("Account disabled. Contact admin.")
        if bcrypt.checkpw(password.encode(), stored_hash):
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login=? WHERE username=?",
                (datetime.now().isoformat(), username)
            )
            # Audit log
            cursor.execute(
                "INSERT INTO audit_logs (username, action, details) VALUES (?, ?, ?)",
                (username, "LOGIN", f"role={role}")
            )
            conn.commit()
            conn.close()
            _clear_failures(username)
            return {"username": username, "role": role}

    conn.close()
    _record_failure(username)
    return None

def create_user(username, password, role="cashier"):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, hashed, role)
    )
    conn.commit()
    conn.close()

def change_password(username, old_password, new_password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if not row or not bcrypt.checkpw(old_password.encode(), row[0]):
        conn.close()
        raise Exception("Current password incorrect.")
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    conn.commit()
    conn.close()

def deactivate_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active=0 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    import pandas as pd
    df = pd.read_sql_query(
        "SELECT id, username, role, created_at, last_login, is_active FROM users", conn
    )
    conn.close()
    return df

def log_action(username, action, details=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (username, action, details) VALUES (?, ?, ?)",
        (username, action, details)
    )
    conn.commit()
    conn.close()

def get_audit_logs():
    conn = get_connection()
    import pandas as pd
    df = pd.read_sql_query(
        "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 500", conn
    )
    conn.close()
    return df

def require_admin(user):
    if user["role"] != "admin":
        raise Exception("Admin access only.")

# Init on import
create_users_table()
initialize_users()
