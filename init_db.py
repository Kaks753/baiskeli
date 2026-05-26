"""
init_db.py — Creates all tables and seeds default users.
Works on both SQLite (local) and PostgreSQL (Render).

Called once at startup from app.py. Safe to call multiple times —
CREATE TABLE IF NOT EXISTS means it never recreates existing tables.

WHY TWO SCHEMAS:
  SQLite requires INTEGER PRIMARY KEY for auto-increment to work.
  Using SERIAL (Postgres syntax) causes SQLite to store NULL as the id,
  which then breaks FOREIGN KEY constraints.
  PostgreSQL uses SERIAL PRIMARY KEY.
  We detect the backend and use the right schema.
"""

import os
import bcrypt
from db_config import get_connection, USE_POSTGRES, DATABASE_URL, DB_PATH


# ── PostgreSQL schema ─────────────────────────────────────────────────────────
SCHEMA_POSTGRES = """
CREATE TABLE IF NOT EXISTS products (
    id               SERIAL PRIMARY KEY,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL,
    subcategory      TEXT,
    size             TEXT,
    brand            TEXT,
    description      TEXT,
    cost_price       DOUBLE PRECISION,
    selling_price    DOUBLE PRECISION NOT NULL,
    quantity_in_stock INTEGER DEFAULT 0,
    reorder_level    INTEGER DEFAULT 5,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    id             SERIAL PRIMARY KEY,
    total_amount   DOUBLE PRECISION NOT NULL,
    payment_method TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type           TEXT DEFAULT 'sale',
    reference_id   INTEGER,
    customer_name  TEXT DEFAULT 'Walk-in',
    discount       DOUBLE PRECISION DEFAULT 0,
    amount_paid    DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS sale_items (
    id         SERIAL PRIMARY KEY,
    sale_id    INTEGER REFERENCES sales(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER,
    price      DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS inventory_logs (
    id         SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    change     INTEGER,
    reason     TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id         SERIAL PRIMARY KEY,
    name       TEXT,
    phone      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    id          SERIAL PRIMARY KEY,
    description TEXT,
    price       DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS parking (
    id               SERIAL PRIMARY KEY,
    customer_name    TEXT,
    bike_description TEXT,
    start_time       TIMESTAMP,
    end_time         TIMESTAMP,
    fee              DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS repairs (
    id            SERIAL PRIMARY KEY,
    customer_name TEXT,
    phone         TEXT,
    bike_type     TEXT,
    issue         TEXT,
    service_cost  DOUBLE PRECISION,
    status        TEXT DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_items (
    id         SERIAL PRIMARY KEY,
    repair_id  INTEGER REFERENCES repairs(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER,
    price      DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    role       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active  INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         SERIAL PRIMARY KEY,
    username   TEXT,
    action     TEXT,
    details    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# ── SQLite schema ─────────────────────────────────────────────────────────────
# Must use INTEGER PRIMARY KEY (not SERIAL) for auto-increment to work in SQLite.
# SERIAL is a Postgres-only keyword; SQLite treats it as TEXT affinity,
# which causes NULLs to be stored as the id — breaking FK constraints.
SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS products (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT NOT NULL,
    category          TEXT NOT NULL,
    subcategory       TEXT,
    size              TEXT,
    brand             TEXT,
    description       TEXT,
    cost_price        REAL,
    selling_price     REAL NOT NULL,
    quantity_in_stock INTEGER DEFAULT 0,
    reorder_level     INTEGER DEFAULT 5,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    total_amount   REAL NOT NULL,
    payment_method TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type           TEXT DEFAULT 'sale',
    reference_id   INTEGER,
    customer_name  TEXT DEFAULT 'Walk-in',
    discount       REAL DEFAULT 0,
    amount_paid    REAL
);

CREATE TABLE IF NOT EXISTS sale_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id    INTEGER REFERENCES sales(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER,
    price      REAL
);

CREATE TABLE IF NOT EXISTS inventory_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    change     INTEGER,
    reason     TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT,
    phone      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    price       REAL
);

CREATE TABLE IF NOT EXISTS parking (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name    TEXT,
    bike_description TEXT,
    start_time       TIMESTAMP,
    end_time         TIMESTAMP,
    fee              REAL
);

CREATE TABLE IF NOT EXISTS repairs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone         TEXT,
    bike_type     TEXT,
    issue         TEXT,
    service_cost  REAL,
    status        TEXT DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id  INTEGER REFERENCES repairs(id),
    product_id INTEGER REFERENCES products(id),
    quantity   INTEGER,
    price      REAL
);

CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT UNIQUE NOT NULL,
    password   TEXT NOT NULL,
    role       TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active  INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT,
    action     TEXT,
    details    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db():
    conn   = get_connection()
    cursor = conn.cursor()

    if USE_POSTGRES:
        # PostgreSQL: execute each statement separately
        for statement in SCHEMA_POSTGRES.strip().split(";"):
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
    else:
        # SQLite: executescript is efficient and handles multiple statements
        conn.executescript(SCHEMA_SQLITE)

    _seed_default_users(cursor)
    conn.commit()
    conn.close()

    label = f"PostgreSQL ({DATABASE_URL[:40]}...)" if USE_POSTGRES \
            else f"SQLite ({DB_PATH})"
    print(f"✅ Database ready: {label}")


def _seed_default_users(cursor):
    """Insert admin + cashier accounts if they don't exist yet."""
    p = "%s" if USE_POSTGRES else "?"

    defaults = [
        ("admin",   "admin2026",   "admin"),
        ("cashier", "cashier2026", "cashier"),
    ]
    for username, password, role in defaults:
        cursor.execute(f"SELECT id FROM users WHERE username={p}", (username,))
        if not cursor.fetchone():
            # .decode() converts bytes → str for Postgres TEXT column
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                f"INSERT INTO users (username, password, role) VALUES ({p},{p},{p})",
                (username, hashed, role),
            )
            print(f"  ✅ Default user created: {username} ({role})")


if __name__ == "__main__":
    init_db()
