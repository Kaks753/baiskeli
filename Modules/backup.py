"""
backup.py — Data export and backup utilities.
Only admin can trigger exports. Data cannot be downloaded by cashier.
"""
import sqlite3
import shutil
import os
import io
from datetime import datetime

DB_NAME = "Databases/baiskeli.db"
BACKUP_DIR = "Backups"

def get_connection():
    return sqlite3.connect(DB_NAME)

def backup_database():
    """Create a timestamped copy of the database file. Returns the backup path."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"baiskeli_backup_{timestamp}.db")
    shutil.copy2(DB_NAME, backup_path)
    return backup_path

def export_to_excel():
    """Export all key tables to an Excel file in memory. Returns BytesIO buffer."""
    import pandas as pd
    conn = get_connection()

    tables = {
        "Sales":     "SELECT * FROM sales ORDER BY created_at DESC",
        "Sale Items":"SELECT si.*, p.name as product_name FROM sale_items si JOIN products p ON si.product_id=p.id",
        "Products":  "SELECT * FROM products",
        "Repairs":   "SELECT * FROM repairs ORDER BY created_at DESC",
        "Parking":   "SELECT * FROM parking ORDER BY start_time DESC",
        "Inventory Log": "SELECT il.*, p.name FROM inventory_logs il JOIN products p ON il.product_id=p.id ORDER BY il.created_at DESC LIMIT 1000",
    }

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, query in tables.items():
            try:
                df = pd.read_sql_query(query, conn)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception:
                pass  # Skip tables that fail
    conn.close()
    buffer.seek(0)
    return buffer

def list_backups():
    """Return list of existing backup files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")]
    files.sort(reverse=True)
    return files

def read_backup(filename):
    """Return bytes of a backup file for download."""
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, "rb") as f:
        return f.read()
