"""
db_config.py — Database connection that works on both SQLite (local)
and PostgreSQL (Render free tier).

HOW IT DECIDES WHICH DATABASE TO USE
======================================
1. If DATABASE_URL env variable is set → connect to PostgreSQL.
   Render sets this automatically when you attach a Postgres database.
2. If BAISKELI_DB_PATH is set → use that file path for SQLite.
3. Otherwise → default SQLite at <repo-root>/Databases/baiskeli.db

WHY POSTGRES ON RENDER FREE TIER
==================================
Render's free web service has NO persistent disk — the filesystem resets
every time the container restarts (after 15 min idle, every redeploy,
or any crash). SQLite is a file. File gets wiped. Data gone.

Render DOES offer a free PostgreSQL database (separate service, survives
restarts permanently). That's where we store data when deployed on Render.

HOW TO SET UP ON RENDER
=========================
1. Render dashboard → New → PostgreSQL → Free tier → Create
   (name it "baiskeli-db")
2. Copy the "Internal Database URL" from the database service page
3. Your web service → Environment tab → Add variable:
      DATABASE_URL = <paste the internal URL here>
4. Manual Deploy → Deploy latest commit
   Data now lives in Postgres and survives forever.
"""

import os
import sqlite3


# ── Detect which database backend to use ─────────────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES  = bool(DATABASE_URL)


# ── SQLite path (only used when not on Postgres) ──────────────────────────────

def _get_sqlite_path() -> str:
    env_path = os.environ.get("BAISKELI_DB_PATH", "").strip()
    if env_path:
        os.makedirs(os.path.dirname(os.path.abspath(env_path)), exist_ok=True)
        return env_path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_dir   = os.path.join(base_dir, "Databases")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "baiskeli.db")


DB_PATH = None if USE_POSTGRES else _get_sqlite_path()


# ── Connection factory ────────────────────────────────────────────────────────

def get_connection():
    """
    Return a database connection — PostgreSQL if DATABASE_URL is set,
    SQLite otherwise.

    Both return a connection that supports .cursor(), .execute(),
    .commit(), .close() — same interface for all callers.

    SQLite extras: WAL mode, foreign keys ON, 30-second timeout.
    Postgres: autocommit off by default, so each caller must .commit().
    """
    if USE_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn


def placeholder(n: int = 1) -> str:
    """
    Return the right SQL placeholders for the active backend.
    SQLite uses  ?   →  placeholder(3) = "?, ?, ?"
    Postgres uses %s →  placeholder(3) = "%s, %s, %s"
    """
    p = "%s" if USE_POSTGRES else "?"
    return ", ".join([p] * n)


def ph() -> str:
    """Single placeholder — shorthand for placeholder(1)."""
    return "%s" if USE_POSTGRES else "?"
