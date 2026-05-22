"""
backup.py — Data export and backup utilities.
Only admin can trigger these. Cashiers cannot export.
"""
import shutil
import os
import io
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import DB_PATH, get_connection

# Keep Backups/ next to the database file (not relative to cwd)
BACKUP_DIR = os.path.join(os.path.dirname(DB_PATH), "..", "Backups")
BACKUP_DIR = os.path.abspath(BACKUP_DIR)


def backup_database() -> str:
    """Create a timestamped copy of the database. Returns the backup path."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"baiskeli_backup_{timestamp}.db")
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def export_to_excel() -> io.BytesIO:
    """Export all key tables to an in-memory Excel file."""
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
                pass  # skip tables that fail silently
    conn.close()
    buffer.seek(0)
    return buffer


def list_backups() -> list:
    """Return list of existing backup filenames, newest first."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(reverse=True)
    return files


def read_backup(filename: str) -> bytes:
    """Return bytes of a backup file for download."""
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, "rb") as f:
        return f.read()
