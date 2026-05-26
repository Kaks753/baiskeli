"""
auth.py — Authentication: bcrypt passwords, brute-force protection, audit logging.
Works on both SQLite and PostgreSQL.

KEY CHANGE vs old version:
  - _p placeholder is "%s" for Postgres, "?" for SQLite
  - bcrypt hash is always normalised to bytes before checkpw()
    (Postgres returns TEXT str; SQLite can return bytes or str)
  - Removed auto-calls to create_users_table() / initialize_users()
    at module bottom — those caused a race condition when multiple
    browser tabs opened simultaneously on startup
"""
import bcrypt
import time
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES

_p = "%s" if USE_POSTGRES else "?"   # SQL placeholder for this backend

# ── In-memory brute-force protection ─────────────────────────────────────────
_failed_attempts: dict = {}
MAX_ATTEMPTS    = 5
LOCKOUT_SECONDS = 300   # 5 minutes


def _is_locked_out(username: str) -> bool:
    now    = time.time()
    recent = [t for t in _failed_attempts.get(username, []) if now - t < LOCKOUT_SECONDS]
    _failed_attempts[username] = recent
    return len(recent) >= MAX_ATTEMPTS

def _record_failure(username: str):
    _failed_attempts.setdefault(username, []).append(time.time())

def _clear_failures(username: str):
    _failed_attempts.pop(username, None)


# ── Auth functions ────────────────────────────────────────────────────────────

def login(username: str, password: str):
    if _is_locked_out(username):
        remaining = int(LOCKOUT_SECONDS - (time.time() - min(_failed_attempts[username])))
        raise Exception(f"Account locked. Try again in {remaining//60}m {remaining%60}s.")

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT password, role, is_active FROM users WHERE username={_p}", (username,)
    )
    row = cursor.fetchone()

    if row:
        stored_hash, role, is_active = row
        if not is_active:
            conn.close()
            raise Exception("Account disabled. Contact admin.")

        # Postgres stores TEXT; SQLite can store bytes or str — normalise to bytes
        hash_bytes = stored_hash.encode() if isinstance(stored_hash, str) else stored_hash

        if bcrypt.checkpw(password.encode(), hash_bytes):
            cursor.execute(
                f"UPDATE users SET last_login={_p} WHERE username={_p}",
                (datetime.now().isoformat(), username)
            )
            cursor.execute(
                f"INSERT INTO audit_logs (username, action, details) VALUES ({_p},{_p},{_p})",
                (username, "LOGIN", f"role={role}")
            )
            conn.commit()
            conn.close()
            _clear_failures(username)
            return {"username": username, "role": role}

    conn.close()
    _record_failure(username)
    return None


def create_user(username: str, password: str, role: str = "cashier"):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO users (username, password, role) VALUES ({_p},{_p},{_p})",
        (username, hashed, role)
    )
    conn.commit()
    conn.close()


def change_password(username: str, old_password: str, new_password: str):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT password FROM users WHERE username={_p}", (username,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("User not found.")
    hash_bytes = row[0].encode() if isinstance(row[0], str) else row[0]
    if not bcrypt.checkpw(old_password.encode(), hash_bytes):
        conn.close()
        raise Exception("Current password is incorrect.")
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        f"UPDATE users SET password={_p} WHERE username={_p}", (hashed, username)
    )
    conn.commit()
    conn.close()


def deactivate_user(username: str):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET is_active=0 WHERE username={_p}", (username,))
    conn.commit()
    conn.close()


def get_all_users():
    import pandas as pd
    conn = get_connection()
    df   = pd.read_sql_query(
        "SELECT id, username, role, created_at, last_login, is_active FROM users", conn
    )
    conn.close()
    return df


def log_action(username: str, action: str, details: str = ""):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT INTO audit_logs (username, action, details) VALUES ({_p},{_p},{_p})",
        (username, action, details)
    )
    conn.commit()
    conn.close()


def get_audit_logs():
    import pandas as pd
    conn = get_connection()
    df   = pd.read_sql_query(
        "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 500", conn
    )
    conn.close()
    return df


def require_admin(user):
    if user["role"] != "admin":
        raise Exception("Admin access only.")
