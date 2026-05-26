"""
inventory.py — Product inventory management.
Works on both SQLite and PostgreSQL.

KEY CHANGES vs old version:
  - _p = "%s" for Postgres, "?" for SQLite
  - After INSERT, we get the new row's ID differently per backend:
      Postgres: SELECT lastval()  (returns the last SERIAL value generated)
      SQLite:   cursor.lastrowid  (built-in attribute)
"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES

_p = "%s" if USE_POSTGRES else "?"


def add_product(name, category, subcategory, brand, size, description,
                cost_price, selling_price, quantity):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO products
            (name, category, subcategory, brand, size, description,
             cost_price, selling_price, quantity_in_stock)
        VALUES ({_p},{_p},{_p},{_p},{_p},{_p},{_p},{_p},{_p})
    """, (name, category, subcategory, brand, size, description,
          cost_price, selling_price, quantity))

    # Get the ID of the row we just inserted
    if USE_POSTGRES:
        cursor.execute("SELECT lastval()")
        product_id = cursor.fetchone()[0]
    else:
        product_id = cursor.lastrowid

    # Log the initial stock entry
    cursor.execute(
        f"INSERT INTO inventory_logs (product_id, change, reason) VALUES ({_p},{_p},{_p})",
        (product_id, quantity, "initial stock")
    )
    conn.commit()
    conn.close()


def restock_product(product_id, quantity):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE products SET quantity_in_stock = quantity_in_stock + {_p} WHERE id = {_p}",
        (quantity, product_id)
    )
    cursor.execute(
        f"INSERT INTO inventory_logs (product_id, change, reason) VALUES ({_p},{_p},{_p})",
        (product_id, quantity, "restock")
    )
    conn.commit()
    conn.close()


def reduce_stock(product_id, quantity):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT quantity_in_stock FROM products WHERE id = {_p}", (product_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise Exception("Product not found")
    if result[0] < quantity:
        conn.close()
        raise Exception("Not enough stock")
    cursor.execute(
        f"UPDATE products SET quantity_in_stock = quantity_in_stock - {_p} WHERE id = {_p}",
        (quantity, product_id)
    )
    cursor.execute(
        f"INSERT INTO inventory_logs (product_id, change, reason) VALUES ({_p},{_p},{_p})",
        (product_id, -quantity, "sale")
    )
    conn.commit()
    conn.close()


def get_all_products():
    conn  = get_connection()
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
    df   = pd.read_sql_query("""
        SELECT name, quantity_in_stock, reorder_level
        FROM products WHERE quantity_in_stock <= reorder_level
    """, conn)
    conn.close()
    return df


def update_product(product_id, name, category, subcategory, brand, size,
                   description, cost, price):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE products
        SET name={_p}, category={_p}, subcategory={_p}, brand={_p},
            size={_p}, description={_p}, cost_price={_p}, selling_price={_p}
        WHERE id={_p}
    """, (name, category, subcategory, brand, size, description, cost, price, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM products WHERE id={_p}", (product_id,))
    conn.commit()
    conn.close()


def get_inventory_log():
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT il.id, p.name, il.change, il.reason, il.created_at
        FROM inventory_logs il
        JOIN products p ON il.product_id = p.id
        ORDER BY il.created_at DESC LIMIT 200
    """, conn)
    conn.close()
    return df
