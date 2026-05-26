"""
parking.py — Bicycle parking check-in / check-out.
Works on both SQLite and PostgreSQL.

KEY CHANGES vs old version:
  - _p placeholder, lastrowid vs lastval()
  - str(row[0]).split(".")[0] strips microseconds from Postgres timestamps
    before passing to datetime.fromisoformat() — Postgres includes them,
    SQLite doesn't, and fromisoformat() chokes on microseconds in Python 3.10-
"""
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES

_p = "%s" if USE_POSTGRES else "?"


def check_in(customer_name: str, bike_description: str, daily_rate: float = 100.0) -> int:
    """
    Register a bike arriving for parking.
    daily_rate is stored in the fee column at check-in time so
    check_out() knows the rate to charge per hour.
    Returns the parking ID to give to the customer.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO parking (customer_name, bike_description, start_time, fee)
        VALUES ({_p},{_p},{_p},{_p})
    """, (customer_name, bike_description, datetime.now().isoformat(), daily_rate))

    if USE_POSTGRES:
        cursor.execute("SELECT lastval()")
        parking_id = cursor.fetchone()[0]
    else:
        parking_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return parking_id


def check_out(parking_id: int):
    """
    Mark a bike as collected, calculate and store the fee.
    Returns (fee_charged, hours_parked).
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT start_time, fee FROM parking WHERE id={_p}", (parking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise Exception("Parking record not found")

    # Strip microseconds so fromisoformat() works on all Python versions
    start_time  = datetime.fromisoformat(str(row[0]).split(".")[0])
    daily_rate  = row[1]
    end_time    = datetime.now()
    hours       = max(1, (end_time - start_time).total_seconds() / 3600)
    hourly_rate = daily_rate / 24
    fee         = round(hours * hourly_rate, 2)

    cursor.execute(f"""
        UPDATE parking SET end_time={_p}, fee={_p} WHERE id={_p}
    """, (end_time.isoformat(), fee, parking_id))
    conn.commit()
    conn.close()
    return fee, hours


def get_active_parking() -> pd.DataFrame:
    """Returns all bikes currently parked (no end_time yet)."""
    conn = get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT id, customer_name, bike_description, start_time,
                   fee AS daily_rate
            FROM parking
            WHERE end_time IS NULL
            ORDER BY start_time ASC
        """, conn)
    except Exception as e:
        print("Parking query error:", e)
        df = pd.DataFrame()
    conn.close()
    return df


def get_parking_history() -> pd.DataFrame:
    """Returns all completed parking sessions."""
    conn = get_connection()
    df   = pd.read_sql_query("""
        SELECT id, customer_name, bike_description, start_time, end_time, fee
        FROM parking
        WHERE end_time IS NOT NULL
        ORDER BY end_time DESC
    """, conn)
    conn.close()
    return df
