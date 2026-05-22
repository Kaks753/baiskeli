

import sqlite3
import pandas as pd

DB_NAME = "Databases/baiskeli.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def add_product(name, category, subcategory, brand, size, description, cost_price, selling_price, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products
        (name, category, subcategory, brand, size, description, cost_price, selling_price, quantity_in_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, subcategory, brand, size, description, cost_price, selling_price, quantity))
    product_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO inventory_logs (product_id, change, reason) VALUES (?, ?, ?)
    """, (product_id, quantity, "initial stock"))
    conn.commit()
    conn.close()

def restock_product(product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products SET quantity_in_stock = quantity_in_stock + ? WHERE id = ?
    """, (quantity, product_id))
    cursor.execute("""
        INSERT INTO inventory_logs (product_id, change, reason) VALUES (?, ?, ?)
    """, (product_id, quantity, "restock"))
    conn.commit()
    conn.close()

def reduce_stock(product_id, quantity):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantity_in_stock FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise Exception("Product not found")
    if result[0] < quantity:
        conn.close()
        raise Exception("Not enough stock")
    cursor.execute("""
        UPDATE products SET quantity_in_stock = quantity_in_stock - ? WHERE id = ?
    """, (quantity, product_id))
    cursor.execute("""
        INSERT INTO inventory_logs (product_id, change, reason) VALUES (?, ?, ?)
    """, (product_id, -quantity, "sale"))
    conn.commit()
    conn.close()

def get_all_products():
    conn = get_connection()
    query = """
        SELECT id, name, category, subcategory, brand, size, description,
               cost_price, selling_price, quantity_in_stock, reorder_level
        FROM products ORDER BY name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df.columns = ["ID", "Name", "Category", "Subcategory", "Brand", "Size",
                  "Description", "Cost Price", "Selling Price", "Stock", "Reorder Level"]
    return df

def get_low_stock():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT name, quantity_in_stock, reorder_level
        FROM products WHERE quantity_in_stock <= reorder_level
    """, conn)
    conn.close()
    return df

def update_product(product_id, name, category, subcategory, brand, size, description, cost, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET name=?, category=?, subcategory=?, brand=?, size=?, description=?,
            cost_price=?, selling_price=?
        WHERE id=?
    """, (name, category, subcategory, brand, size, description, cost, price, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def get_inventory_log():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT il.id, p.name, il.change, il.reason, il.created_at
        FROM inventory_logs il
        JOIN products p ON il.product_id = p.id
        ORDER BY il.created_at DESC LIMIT 200
    """, conn)
    conn.close()
    return df
