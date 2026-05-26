"""
repairs.py — Bicycle repair job management.
Works on both SQLite and PostgreSQL.

KEY CHANGES vs old version:
  - _p placeholder, lastrowid vs lastval()
  - get_repairs() uses STRING_AGG (Postgres) vs GROUP_CONCAT (SQLite)
    for combining multiple parts into one readable column
"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES
from Modules.inventory import reduce_stock

_p = "%s" if USE_POSTGRES else "?"


def create_repair(customer_name, phone, bike_type, issue, service_cost):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO repairs (customer_name, phone, bike_type, issue, service_cost)
        VALUES ({_p},{_p},{_p},{_p},{_p})
    """, (customer_name, phone, bike_type, issue, service_cost))

    if USE_POSTGRES:
        cursor.execute("SELECT lastval()")
        repair_id = cursor.fetchone()[0]
    else:
        repair_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return repair_id


def add_repair_item(repair_id, product_id, quantity, price):
    reduce_stock(product_id, quantity)
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO repair_items (repair_id, product_id, quantity, price)
        VALUES ({_p},{_p},{_p},{_p})
    """, (repair_id, product_id, quantity, price))
    conn.commit()
    conn.close()


def get_repairs():
    """
    Returns all repairs with a human-readable 'parts_used' column.
    STRING_AGG is PostgreSQL; GROUP_CONCAT is SQLite — same purpose.
    """
    try:
        conn = get_connection()
        if USE_POSTGRES:
            query = """
            SELECT
                r.id, r.customer_name, r.phone, r.bike_type, r.issue,
                r.service_cost, r.status, r.created_at,
                STRING_AGG(
                    p.name || ' x' || ri.quantity || ' (KES ' || ri.price || ')',
                    ', '
                ) AS parts_used
            FROM repairs r
            LEFT JOIN repair_items ri ON r.id = ri.repair_id
            LEFT JOIN products      p  ON ri.product_id = p.id
            GROUP BY r.id, r.customer_name, r.phone, r.bike_type,
                     r.issue, r.service_cost, r.status, r.created_at
            ORDER BY r.created_at DESC
            """
        else:
            query = """
            SELECT
                r.id, r.customer_name, r.phone, r.bike_type, r.issue,
                r.service_cost, r.status, r.created_at,
                GROUP_CONCAT(
                    p.name || ' x' || ri.quantity || ' (KES ' || ri.price || ')', ', '
                ) AS parts_used
            FROM repairs r
            LEFT JOIN repair_items ri ON r.id = ri.repair_id
            LEFT JOIN products      p  ON ri.product_id = p.id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def get_repair_items(repair_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT p.id, p.name, ri.quantity, ri.price
        FROM repair_items ri
        JOIN products p ON ri.product_id = p.id
        WHERE ri.repair_id={_p}
    """, (repair_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"product_id": r[0], "name": r[1], "qty": r[2], "price": r[3]} for r in rows]


def get_repair_service_cost(repair_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT service_cost FROM repairs WHERE id={_p}", (repair_id,))
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0


def get_repair_details(repair_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT customer_name, phone, bike_type, issue FROM repairs WHERE id={_p}
    """, (repair_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"customer_name": row[0], "phone": row[1],
                "bike_type": row[2], "issue": row[3]}
    return {}


def record_repair_sale(repair_id, payment_method="Cash",
                       discount=0.0, amount_paid=None):
    conn   = get_connection()
    cursor = conn.cursor()

    # Guard: don't double-record if already paid
    cursor.execute(
        f"SELECT id FROM sales WHERE reference_id={_p} AND type='repair'", (repair_id,)
    )
    if cursor.fetchone():
        conn.close()
        return

    parts        = get_repair_items(repair_id)
    service_cost = get_repair_service_cost(repair_id)
    total_parts  = sum(float(p["qty"]) * float(p["price"]) for p in parts)
    total_amount = max(0, total_parts + service_cost - float(discount))
    if amount_paid is None:
        amount_paid = total_amount

    repair   = get_repair_details(repair_id)
    customer = repair.get("customer_name", "Walk-in")

    cursor.execute(f"""
        INSERT INTO sales
            (created_at, total_amount, type, reference_id,
             customer_name, payment_method, discount, amount_paid)
        VALUES (CURRENT_TIMESTAMP,{_p},'repair',{_p},{_p},{_p},{_p},{_p})
    """, (total_amount, repair_id, customer, payment_method, discount, amount_paid))

    if USE_POSTGRES:
        cursor.execute("SELECT lastval()")
        sale_id = cursor.fetchone()[0]
    else:
        sale_id = cursor.lastrowid

    for p in parts:
        if not p.get("product_id"):
            continue
        cursor.execute(f"""
            INSERT INTO sale_items (sale_id, product_id, quantity, price)
            VALUES ({_p},{_p},{_p},{_p})
        """, (sale_id, p["product_id"], p["qty"], p["price"]))

    conn.commit()
    conn.close()


def update_repair_status(repair_id, status):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE repairs SET status={_p} WHERE id={_p}", (status, repair_id))
    conn.commit()
    conn.close()


def delete_repair(repair_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM repair_items WHERE repair_id={_p}", (repair_id,))
    cursor.execute(f"DELETE FROM repairs WHERE id={_p}", (repair_id,))
    conn.commit()
    conn.close()
