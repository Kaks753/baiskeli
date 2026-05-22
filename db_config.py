"""
db_config.py — Single source of truth for the database path.

THE CORE PROBLEM (why data kept vanishing):
============================================
Streamlit Cloud (and many other cloud platforms) runs your app inside an
ephemeral container.  Every time the dyno/container restarts — which can
happen after a period of inactivity, a new deploy, or just the platform
deciding to cycle workers — the entire filesystem is wiped and recreated
from the Docker image.

SQLite is a *file*.  If that file lives inside the container's local
filesystem, it disappears with the container.  Your data is gone.

THE FIX:
=========
1. Local / self-hosted  →  the default path (Databases/baiskeli.db anchored
   to this file's directory) works perfectly — data survives restarts
   because the disk is persistent.

2. Railway / Render / Fly.io with a persistent volume  →  mount a volume
   (e.g. /data) and set the env variable:
       BAISKELI_DB_PATH=/data/baiskeli.db
   The volume survives container restarts.  This is the recommended
   production setup.

3. Streamlit Cloud  →  Streamlit Cloud does NOT offer persistent disk.
   You have two options:
     a) Switch to Railway/Render (recommended — free tier available).
     b) Use a hosted Postgres/MySQL + swap the sqlite3 calls for
        SQLAlchemy (bigger change, not done here).
   The env-variable override still works if you somehow mount external
   storage via a custom Docker layer, but that's advanced.

HOW TO SET THE ENV VAR:
  • Railway:  Settings → Variables → Add Variable
  • Render:   Environment → Add Environment Variable
  • Local:    export BAISKELI_DB_PATH=/path/to/your/baiskeli.db
  • .streamlit/secrets.toml:
        [env]
        BAISKELI_DB_PATH = "/data/baiskeli.db"

You can also just drop the db wherever you like and point here.
"""

import os
import sqlite3


def get_db_path() -> str:
    """Return the absolute path to the SQLite database file."""

    # 1. Honour an explicit override — recommended for production deploys
    env_path = os.environ.get("BAISKELI_DB_PATH", "").strip()
    if env_path:
        os.makedirs(os.path.dirname(os.path.abspath(env_path)), exist_ok=True)
        return env_path

    # 2. Default: <repo-root>/Databases/baiskeli.db  — always absolute,
    #    anchored to THIS file so changing cwd never matters.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir   = os.path.join(base_dir, "Databases")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "baiskeli.db")


def get_connection(timeout: int = 30) -> sqlite3.Connection:
    """
    Return a SQLite connection with sensible defaults:
      • WAL journal mode  — allows concurrent reads during a write,
        drastically reduces "database is locked" errors when multiple
        Streamlit sessions hit the DB at the same time.
      • Foreign key enforcement
      • 30-second busy timeout so a slow write doesn't immediately
        crash a second session with "database is locked".
    """
    conn = sqlite3.connect(DB_PATH, timeout=timeout)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")   # safe with WAL, faster
    return conn


# Ready-to-use constant — every module does:
#   from db_config import DB_PATH, get_connection
DB_PATH = get_db_path()
