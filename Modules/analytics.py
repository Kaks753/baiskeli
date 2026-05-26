"""
analytics.py — Sales, repairs, and parking analytics queries.
Works on both SQLite and PostgreSQL.

KEY CHANGES vs old version:
  - _date_filter() returns different SQL date functions per backend:
      Postgres: CURRENT_DATE, DATE_TRUNC, INTERVAL
      SQLite:   DATE('now'), strftime()
  - _month_group() returns TO_CHAR (Postgres) vs strftime (SQLite)
  These SQL functions are not interchangeable between the two databases,
  so we branch on USE_POSTGRES wherever date arithmetic is needed.
"""
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_config import get_connection, USE_POSTGRES


def _date_filter(filter_type: str, col: str) -> str:
    """Return a WHERE clause fragment for the given date column."""
    if USE_POSTGRES:
        if filter_type == "Today":
            return f"WHERE DATE({col}) = CURRENT_DATE"
        elif filter_type == "This Week":
            return f"WHERE {col} >= CURRENT_DATE - INTERVAL '7 days'"
        elif filter_type == "This Month":
            return f"WHERE DATE_TRUNC('month', {col}) = DATE_TRUNC('month', CURRENT_DATE)"
        elif filter_type == "Last Month":
            return (f"WHERE DATE_TRUNC('month', {col}) = "
                    f"DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')")
        elif filter_type == "This Year":
            return f"WHERE DATE_TRUNC('year', {col}) = DATE_TRUNC('year', CURRENT_DATE)"
        return ""   # "All" — no filter
    else:
        if filter_type == "Today":
            return f"WHERE DATE({col}) = DATE('now')"
        elif filter_type == "This Week":
            return f"WHERE DATE({col}) >= DATE('now', '-7 days')"
        elif filter_type == "This Month":
            return f"WHERE strftime('%Y-%m', {col}) = strftime('%Y-%m', 'now')"
        elif filter_type == "Last Month":
            return f"WHERE strftime('%Y-%m', {col}) = strftime('%Y-%m', DATE('now','-1 month'))"
        elif filter_type == "This Year":
            return f"WHERE strftime('%Y', {col}) = strftime('%Y', 'now')"
        return ""


def _date_group(col: str) -> str:
    """Daily grouping — DATE() works on both backends."""
    return f"DATE({col})"


def _month_group(col: str) -> str:
    """Monthly grouping expression — syntax differs between backends."""
    if USE_POSTGRES:
        return f"TO_CHAR({col}, 'YYYY-MM')"
    return f"strftime('%Y-%m', {col})"


def get_sales_summary(filter_type: str = "All"):
    conn        = get_connection()
    date_filter = _date_filter(filter_type, "s.created_at")
    query = f"""
    SELECT
        COUNT(DISTINCT s.id)                                       AS total_transactions,
        COALESCE(SUM(si.quantity * si.price), 0)                  AS total_revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS total_profit,
        COALESCE(SUM(si.quantity), 0)                             AS total_units_sold,
        COALESCE(SUM(s.discount), 0)                              AS total_discounts
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products   p  ON si.product_id = p.id
    {date_filter}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0]


def get_daily_sales(filter_type: str = "All"):
    conn        = get_connection()
    date_filter = _date_filter(filter_type, "s.created_at")
    dg          = _date_group("s.created_at")
    query = f"""
    SELECT
        {dg}                                                        AS date,
        COALESCE(SUM(si.quantity * si.price), 0)                  AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS profit,
        COUNT(DISTINCT s.id)                                       AS transactions
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products   p  ON si.product_id = p.id
    {date_filter}
    GROUP BY {dg}
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_monthly_sales():
    conn = get_connection()
    mg   = _month_group("s.created_at")
    query = f"""
    SELECT
        {mg}                                                        AS month,
        COALESCE(SUM(si.quantity * si.price), 0)                  AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS profit
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products   p  ON si.product_id = p.id
    GROUP BY {mg}
    ORDER BY month DESC LIMIT 12
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_top_products(filter_type: str = "All", limit: int = 10):
    conn        = get_connection()
    date_filter = _date_filter(filter_type, "s.created_at")
    query = f"""
    SELECT
        p.name,
        p.category,
        SUM(si.quantity)                                           AS total_sold,
        COALESCE(SUM(si.quantity * si.price), 0)                  AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS profit
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products   p  ON si.product_id = p.id
    {date_filter}
    GROUP BY p.name, p.category
    ORDER BY total_sold DESC
    LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_category_breakdown(filter_type: str = "All"):
    conn        = get_connection()
    date_filter = _date_filter(filter_type, "s.created_at")
    query = f"""
    SELECT
        p.category,
        COALESCE(SUM(si.quantity * si.price), 0) AS revenue,
        COUNT(DISTINCT s.id)                      AS transactions
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products   p  ON si.product_id = p.id
    {date_filter}
    GROUP BY p.category
    ORDER BY revenue DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_payment_breakdown(filter_type: str = "All"):
    conn        = get_connection()
    date_filter = _date_filter(filter_type, "s.created_at")
    query = f"""
    SELECT
        s.payment_method,
        COUNT(*)                          AS count,
        COALESCE(SUM(s.total_amount), 0) AS total
    FROM sales s
    {date_filter}
    GROUP BY s.payment_method
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_repairs_summary(filter_type: str = "All"):
    try:
        conn        = get_connection()
        date_filter = _date_filter(filter_type, "created_at")
        query = f"""
        SELECT
            COUNT(*) AS total_repairs,
            SUM(CASE WHEN status='pending'   THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status='paid'      THEN 1 ELSE 0 END) AS paid
        FROM repairs {date_filter}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0]
    except Exception:
        return pd.Series({"total_repairs": 0, "pending": 0, "completed": 0, "paid": 0})


def get_parking_revenue(filter_type: str = "All"):
    try:
        conn        = get_connection()
        date_filter = _date_filter(filter_type, "end_time")
        if not date_filter:
            date_filter = "WHERE end_time IS NOT NULL"
        else:
            date_filter += " AND end_time IS NOT NULL"
        query = f"""
        SELECT COUNT(*) AS sessions, COALESCE(SUM(fee), 0) AS revenue
        FROM parking {date_filter}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0]
    except Exception:
        return pd.Series({"sessions": 0, "revenue": 0})


def get_full_sales_history():
    conn = get_connection()
    df   = pd.read_sql_query("""
    SELECT
        s.id           AS sale_id,
        s.created_at,
        s.customer_name,
        s.total_amount,
        s.discount,
        s.amount_paid,
        s.payment_method,
        s.type,
        s.reference_id
    FROM sales s
    ORDER BY s.created_at DESC
    """, conn)
    conn.close()
    return df
