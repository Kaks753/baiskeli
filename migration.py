"""
migration.py — Safe, additive-only schema migrations.

Rules:
  • NEVER drop tables or columns here.  Only ADD.
  • To add a future column  →  append a safe_add_column() call.
  • To add a future table   →  add CREATE TABLE IF NOT EXISTS inside run_migrations().
"""

from db_config import DB_PATH, get_connection


def safe_add_column(cursor, table: str, column: str, col_type: str, default=None):
    """Add a column only if it doesn't already exist.  Never raises."""
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in cursor.fetchall()]
        if column not in existing:
            default_clause = f" DEFAULT {default}" if default is not None else ""
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"
            )
            print(f"  ✅ Added column: {table}.{column}")
    except Exception as e:
        print(f"  ⚠️  Skipped {table}.{column}: {e}")


def run_migrations():
    conn   = get_connection()
    cursor = conn.cursor()

    # ── products ──────────────────────────────────────────────────
    safe_add_column(cursor, "products", "brand",       "TEXT")
    safe_add_column(cursor, "products", "description", "TEXT")
    safe_add_column(cursor, "products", "size",        "TEXT")
    safe_add_column(cursor, "products", "subcategory", "TEXT")

    # ── sales ─────────────────────────────────────────────────────
    safe_add_column(cursor, "sales", "type",          "TEXT",    "'sale'")
    safe_add_column(cursor, "sales", "reference_id",  "INTEGER")
    safe_add_column(cursor, "sales", "customer_name", "TEXT",    "'Walk-in'")
    safe_add_column(cursor, "sales", "discount",      "REAL",    "0")
    safe_add_column(cursor, "sales", "amount_paid",   "REAL")

    # ── repair_items ──────────────────────────────────────────────
    safe_add_column(cursor, "repair_items", "price", "REAL", "0")

    # ── users ─────────────────────────────────────────────────────
    safe_add_column(cursor, "users", "last_login", "TIMESTAMP")
    safe_add_column(cursor, "users", "is_active",  "INTEGER", "1")

    # ── audit_logs (create if missing — edge-case safety net) ─────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT,
            action     TEXT,
            details    TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── parking (create if missing) ───────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name    TEXT,
            bike_description TEXT,
            start_time       TIMESTAMP,
            end_time         TIMESTAMP,
            fee              REAL
        )
    """)
    safe_add_column(cursor, "parking", "end_time", "TIMESTAMP")
    safe_add_column(cursor, "parking", "fee",      "REAL")

    conn.commit()
    conn.close()
    print("✅ Migrations complete.")


if __name__ == "__main__":
    run_migrations()
