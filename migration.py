"""
migration.py — Safe, additive-only schema migrations.
Works on both SQLite and PostgreSQL.

Rules:
  • NEVER drop tables or columns — only ADD.
  • safe_add_column() checks if the column already exists before adding.
  • Safe to run on every app startup — never errors on existing columns.

WHY THIS EXISTS:
  The schema in init_db.py covers new installs. This file handles
  existing databases that were created before certain columns existed —
  it adds the missing columns without destroying existing data.
"""

from db_config import get_connection, USE_POSTGRES


def safe_add_column(cursor, table: str, column: str, col_type: str, default=None):
    """Add a column only if it doesn't already exist. Never raises."""
    try:
        if USE_POSTGRES:
            # PostgreSQL: query the information schema
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name=%s AND column_name=%s
            """, (table, column))
            exists = cursor.fetchone()
        else:
            # SQLite: use PRAGMA table_info
            cursor.execute(f"PRAGMA table_info({table})")
            exists = any(row[1] == column for row in cursor.fetchall())

        if not exists:
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

    # ── products ──────────────────────────────────────────────────────────────
    safe_add_column(cursor, "products", "brand",       "TEXT")
    safe_add_column(cursor, "products", "description", "TEXT")
    safe_add_column(cursor, "products", "size",        "TEXT")
    safe_add_column(cursor, "products", "subcategory", "TEXT")

    # ── sales ─────────────────────────────────────────────────────────────────
    safe_add_column(cursor, "sales", "type",          "TEXT",             "'sale'")
    safe_add_column(cursor, "sales", "reference_id",  "INTEGER")
    safe_add_column(cursor, "sales", "customer_name", "TEXT",             "'Walk-in'")
    safe_add_column(cursor, "sales", "discount",      "DOUBLE PRECISION", "0")
    safe_add_column(cursor, "sales", "amount_paid",   "DOUBLE PRECISION")

    # ── repair_items ──────────────────────────────────────────────────────────
    safe_add_column(cursor, "repair_items", "price", "DOUBLE PRECISION", "0")

    # ── users ─────────────────────────────────────────────────────────────────
    safe_add_column(cursor, "users", "last_login", "TIMESTAMP")
    safe_add_column(cursor, "users", "is_active",  "INTEGER", "1")

    # ── parking ───────────────────────────────────────────────────────────────
    safe_add_column(cursor, "parking", "end_time", "TIMESTAMP")
    safe_add_column(cursor, "parking", "fee",      "DOUBLE PRECISION")

    conn.commit()
    conn.close()
    print("✅ Migrations complete.")


if __name__ == "__main__":
    run_migrations()
