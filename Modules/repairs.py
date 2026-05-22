

import sqlite3
import pandas as pd
from Modules.inventory import reduce_stock

DB_NAME = "Databases/baiskeli.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_repair(customer_name, phone, bike_type, issue, service_cost):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO repairs (customer_name, phone, bike_type, issue, service_cost)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_name, phone, bike_type, issue, service_cost))
    repair_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return repair_id

def add_repair_item(repair_id, product_id, quantity, price):
    reduce_stock(product_id, quantity)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO repair_items (repair_id, product_id, quantity, price)
        VALUES (?, ?, ?, ?)
    """, (repair_id, product_id, quantity, price))
    conn.commit()
    conn.close()

def get_repairs():
    try:
        conn = get_connection()
        query = """
        SELECT
            r.id,
            r.customer_name,
            r.phone,
            r.bike_type,
            r.issue,
            r.service_cost,
            r.status,
            r.created_at,
            GROUP_CONCAT(
                p.name || ' x' || ri.quantity || ' (KES ' || ri.price || ')', ', '
            ) AS parts_used
        FROM repairs r
        LEFT JOIN repair_items ri ON r.id = ri.repair_id
        LEFT JOIN products p ON ri.product_id = p.id
        GROUP BY r.id
        ORDER BY r.created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_repair_items(repair_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.name, ri.quantity, ri.price
        FROM repair_items ri
        JOIN products p ON ri.product_id = p.id
        WHERE ri.repair_id=?
    """, (repair_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"product_id": r[0], "name": r[1], "qty": r[2], "price": r[3]} for r in rows]

def get_repair_service_cost(repair_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT service_cost FROM repairs WHERE id=?", (repair_id,))
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def get_repair_details(repair_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT customer_name, phone, bike_type, issue FROM repairs WHERE id=?
    """, (repair_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"customer_name": row[0], "phone": row[1], "bike_type": row[2], "issue": row[3]}
    return {}

def record_repair_sale(repair_id, payment_method="Cash", discount=0.0, amount_paid=None):
    conn = get_connection()
    cursor = conn.cursor()

    # Prevent duplicate sales
    cursor.execute("SELECT id FROM sales WHERE reference_id=? AND type='repair'", (repair_id,))
    if cursor.fetchone():
        conn.close()
        return

    parts = get_repair_items(repair_id)
    service_cost = get_repair_service_cost(repair_id)

    total_parts = sum(float(p["qty"]) * float(p["price"]) for p in parts)
    total_amount = max(0, total_parts + service_cost - float(discount))
    if amount_paid is None:
        amount_paid = total_amount

    repair = get_repair_details(repair_id)
    customer = repair.get("customer_name", "Walk-in")

    cursor.execute("""
        INSERT INTO sales (created_at, total_amount, type, reference_id,
                           customer_name, payment_method, discount, amount_paid)
        VALUES (CURRENT_TIMESTAMP, ?, 'repair', ?, ?, ?, ?, ?)
    """, (total_amount, repair_id, customer, payment_method, discount, amount_paid))

    sale_id = cursor.lastrowid

    for p in parts:
        if not p.get("product_id"):
            continue
        cursor.execute("""
            INSERT INTO sale_items (sale_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (sale_id, p["product_id"], p["qty"], p["price"]))

    conn.commit()
    conn.close()

def update_repair_status(repair_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE repairs SET status=? WHERE id=?", (status, repair_id))
    conn.commit()
    conn.close()

def delete_repair(repair_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM repair_items WHERE repair_id=?", (repair_id,))
    cursor.execute("DELETE FROM repairs WHERE id=?", (repair_id,))
    conn.commit()
    conn.close()
