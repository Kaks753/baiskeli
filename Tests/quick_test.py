import sqlite3

conn = sqlite3.connect("baiskeli.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO products (name, category, selling_price, quantity_in_stock)
VALUES (?, ?, ?, ?)
""", ("Mountain Bike", "bike", 25000, 5))

conn.commit()

cursor.execute("SELECT * FROM products")
print(cursor.fetchall())

conn.close()