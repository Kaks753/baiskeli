import sqlite3

conn = sqlite3.connect("Databases/baiskeli.db")
cursor = conn.cursor()

# ---------------- REPAIRS TABLE ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    bike_type TEXT,
    issue TEXT,
    service_cost REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ---------------- REPAIR ITEMS ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS repair_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY (repair_id) REFERENCES repairs(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# Add price column (per-unit price of part)
cursor.execute("""
    ALTER TABLE repair_items
    ADD COLUMN price REAL DEFAULT 0.0
""")

conn.commit()
conn.close()

print("✅ Repairs tables created successfully!")