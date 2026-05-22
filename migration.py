

"""
migration.py — Safe, additive-only schema migrations.
NEVER drop tables or columns here. Only ADD.
To add future columns: append new safe_add_column() calls.
"""
import sqlite3

DB_NAME = "Databases/baiskeli.db"

def safe_add_column(cursor, table, column, col_type, default=None):
    """Add a column only if it doesn't exist. Never fails."""
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [row[1] for row in cursor.fetchall()]
        if column not in existing:
            default_clause = f" DEFAULT {default}" if default is not None else ""
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}")
            print(f"✅ Added column: {table}.{column}")
    except Exception as e:
        print(f"⚠️ Skipped {table}.{column}: {e}")

def run_migrations():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ---- products ----
    safe_add_column(cursor, "products", "brand", "TEXT")
    safe_add_column(cursor, "products", "description", "TEXT")
    safe_add_column(cursor, "products", "size", "TEXT")
    safe_add_column(cursor, "products", "subcategory", "TEXT")

    # ---- sales ----
    safe_add_column(cursor, "sales", "type", "TEXT", "'sale'")
    safe_add_column(cursor, "sales", "reference_id", "INTEGER")
    safe_add_column(cursor, "sales", "customer_name", "TEXT", "'Walk-in'")
    safe_add_column(cursor, "sales", "discount", "REAL", "0")
    safe_add_column(cursor, "sales", "amount_paid", "REAL")

    # ---- repair_items ----
    safe_add_column(cursor, "repair_items", "price", "REAL", "0")

    # ---- users ----
    safe_add_column(cursor, "users", "last_login", "TIMESTAMP")
    safe_add_column(cursor, "users", "is_active", "INTEGER", "1")

    # ---- audit_logs (create if missing) ----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
        # ---- parking ----
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            bike_description TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            fee REAL
        )
    """)
    safe_add_column(cursor, "parking", "end_time", "TIMESTAMP")
    safe_add_column(cursor, "parking", "fee", "REAL")


    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migrations()
    print("✅ Migrations complete.")
