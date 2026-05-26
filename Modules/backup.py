"""
backup.py — Data export and backup utilities.
Works on both SQLite and PostgreSQL.

KEY CHANGES vs old version:
  - Postgres path: exports every table as CSV text (can't copy a .db file)
  - SQLite path: copies the .db file as before
"""
import shutil, os, io, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES, DB_PATH

_BASE      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(_BASE, "Backups")


def backup_database() -> str:
    """
    SQLite: timestamped file copy → baiskeli_backup_YYYYMMDD_HHMMSS.db
    Postgres: exports all tables as CSV text → baiskeli_backup_YYYYMMDD_HHMMSS.txt
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if USE_POSTGRES:
        import pandas as pd
        conn      = get_connection()
        tables    = ["products", "sales", "sale_items", "inventory_logs",
                     "repairs", "repair_items", "parking", "users", "audit_logs"]
        backup_path = os.path.join(BACKUP_DIR, f"baiskeli_backup_{timestamp}.txt")
        with open(backup_path, "w") as f:
            f.write(f"# Baiskeli Centre POS — Backup {timestamp}\n")
            for table in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    f.write(f"\n## TABLE: {table} ({len(df)} rows)\n")
                    f.write(df.to_csv(index=False))
                except Exception as e:
                    f.write(f"\n## ERROR reading {table}: {e}\n")
        conn.close()
        return backup_path
    else:
        backup_path = os.path.join(BACKUP_DIR, f"baiskeli_backup_{timestamp}.db")
        shutil.copy2(DB_PATH, backup_path)
        return backup_path


def export_to_excel() -> io.BytesIO:
    """Export all key tables to an in-memory Excel file (works on both backends)."""
    import pandas as pd
    conn = get_connection()

    tables = {
        "Sales":         "SELECT * FROM sales ORDER BY created_at DESC",
        "Sale Items":    "SELECT si.*, p.name AS product_name FROM sale_items si "
                         "JOIN products p ON si.product_id=p.id",
        "Products":      "SELECT * FROM products",
        "Repairs":       "SELECT * FROM repairs ORDER BY created_at DESC",
        "Parking":       "SELECT * FROM parking ORDER BY start_time DESC",
        "Inventory Log": "SELECT il.*, p.name FROM inventory_logs il "
                         "JOIN products p ON il.product_id=p.id "
                         "ORDER BY il.created_at DESC LIMIT 1000",
    }

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, query in tables.items():
            try:
                df = pd.read_sql_query(query, conn)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception:
                pass
    conn.close()
    buffer.seek(0)
    return buffer


def list_backups() -> list:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith((".db", ".txt"))]
    files.sort(reverse=True)
    return files


def read_backup(filename: str) -> bytes:
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, "rb") as f:
        return f.read()
