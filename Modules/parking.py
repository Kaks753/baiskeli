

import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "Databases/baiskeli.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def check_in(customer_name, bike_description, daily_rate=100.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parking (customer_name, bike_description, start_time, fee)
        VALUES (?, ?, ?, ?)
    """, (customer_name, bike_description, datetime.now().isoformat(), daily_rate))
    parking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return parking_id

def check_out(parking_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start_time, fee FROM parking WHERE id=?", (parking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("Parking record not found")

    start_time = datetime.fromisoformat(row[0])
    daily_rate = row[1]
    end_time = datetime.now()

    hours = max(1, (end_time - start_time).total_seconds() / 3600)
    hourly_rate = daily_rate / 24
    fee = round(hours * hourly_rate, 2)

    cursor.execute("""
        UPDATE parking SET end_time=?, fee=? WHERE id=?
    """, (end_time.isoformat(), fee, parking_id))
    conn.commit()
    conn.close()
    return fee, hours

def get_active_parking():
    conn = get_connection()

    try:
        df = pd.read_sql_query("""
            SELECT id, customer_name, bike_description, start_time, fee AS daily_rate
            FROM parking
            WHERE end_time IS NULL
            ORDER BY start_time ASC
        """, conn)
    except Exception as e:
        print("Parking query error:", e)
        df = pd.DataFrame()

    conn.close()
    return df

def get_parking_history():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, customer_name, bike_description, start_time, end_time, fee
        FROM parking WHERE end_time IS NOT NULL ORDER BY end_time DESC
    """, conn)
    conn.close()
    return df

