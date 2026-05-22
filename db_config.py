"""
db_config.py — Single source of truth for the database path.

Why this exists:
  The old code used a relative path ("Databases/baiskeli.db") everywhere.
  Relative paths are calculated from whatever the *current working directory*
  is at runtime — and that can change between restarts, deployments, or when
  Streamlit Cloud spins up a new worker.  The result: Python happily creates a
  brand-new empty database in the new cwd and your data looks "gone".

  Fix: resolve an absolute path once, at import time, anchored to the location
  of THIS file.  No matter how the app is started or where from, the database
  will always land in the same physical folder.

  You can also override it with the environment variable BAISKELI_DB_PATH,
  which is useful for:
    • Streamlit Cloud  →  set it to a mounted volume path
    • Docker           →  point to a persistent volume
    • Local dev        →  leave it unset and it just works
"""

import os

def get_db_path() -> str:
    """Return the absolute path to the SQLite database file."""

    # 1. Honour an explicit override (e.g. from Streamlit secrets or .env)
    env_path = os.environ.get("BAISKELI_DB_PATH", "").strip()
    if env_path:
        # Make sure the parent directory exists
        os.makedirs(os.path.dirname(env_path), exist_ok=True)
        return env_path

    # 2. Default: <repo-root>/Databases/baiskeli.db  — always absolute
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir   = os.path.join(base_dir, "Databases")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "baiskeli.db")


# Expose a ready-to-use constant so every module can just do:
#   from db_config import DB_PATH
DB_PATH = get_db_path()
