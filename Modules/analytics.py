


import sqlite3
import pandas as pd

DB_NAME = "Databases/baiskeli.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_date_filter(filter_type, table_alias="s"):
    col = f"{table_alias}.created_at"
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

def get_sales_summary(filter_type="All"):
    conn = get_connection()
    date_filter = get_date_filter(filter_type)
    query = f"""
    SELECT
        COUNT(DISTINCT s.id)                                          AS total_transactions,
        COALESCE(SUM(si.quantity * si.price), 0)                     AS total_revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0)    AS total_profit,
        COALESCE(SUM(si.quantity), 0)                                AS total_units_sold,
        COALESCE(SUM(s.discount), 0)                                 AS total_discounts
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products p ON si.product_id = p.id
    {date_filter}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.iloc[0]

def get_daily_sales(filter_type="All"):
    conn = get_connection()
    date_filter = get_date_filter(filter_type)
    query = f"""
    SELECT
        DATE(s.created_at) AS date,
        COALESCE(SUM(si.quantity * si.price), 0) AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS profit,
        COUNT(DISTINCT s.id) AS transactions
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products p ON si.product_id = p.id
    {date_filter}
    GROUP BY DATE(s.created_at)
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_monthly_sales():
    conn = get_connection()
    query = """
    SELECT
        strftime('%Y-%m', s.created_at) AS month,
        COALESCE(SUM(si.quantity * si.price), 0) AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)), 0) AS profit
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products p ON si.product_id = p.id
    GROUP BY strftime('%Y-%m', s.created_at)
    ORDER BY month DESC LIMIT 12
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_top_products(filter_type="All", limit=10):
    conn = get_connection()
    date_filter = get_date_filter(filter_type)
    query = f"""
    SELECT
        p.name,
        p.category,
        SUM(si.quantity)                                         AS total_sold,
        COALESCE(SUM(si.quantity * si.price), 0)                AS revenue,
        COALESCE(SUM(si.quantity * (si.price - p.cost_price)),0) AS profit
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products p ON si.product_id = p.id
    {date_filter}
    GROUP BY p.name, p.category
    ORDER BY total_sold DESC
    LIMIT {limit}
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_category_breakdown(filter_type="All"):
    conn = get_connection()
    date_filter = get_date_filter(filter_type)
    query = f"""
    SELECT
        p.category,
        COALESCE(SUM(si.quantity * si.price), 0) AS revenue,
        COUNT(DISTINCT s.id) AS transactions
    FROM sales s
    JOIN sale_items si ON s.id = si.sale_id
    JOIN products p ON si.product_id = p.id
    {date_filter}
    GROUP BY p.category
    ORDER BY revenue DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_payment_breakdown(filter_type="All"):
    conn = get_connection()
    date_filter = get_date_filter(filter_type)
    query = f"""
    SELECT
        s.payment_method,
        COUNT(*) AS count,
        COALESCE(SUM(s.total_amount), 0) AS total
    FROM sales s
    {date_filter}
    GROUP BY s.payment_method
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_repairs_summary(filter_type="All"):
    try:
        conn = get_connection()
        if filter_type == "Today":
            wh = "WHERE DATE(created_at) = DATE('now')"
        elif filter_type == "This Week":
            wh = "WHERE DATE(created_at) >= DATE('now','-7 days')"
        elif filter_type == "This Month":
            wh = "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m','now')"
        else:
            wh = ""
        query = f"""
        SELECT
            COUNT(*) AS total_repairs,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) AS paid
        FROM repairs {wh}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0]
    except Exception:
        import pandas as pd
        return pd.Series({"total_repairs": 0, "pending": 0, "completed": 0, "paid": 0})

def get_parking_revenue(filter_type="All"):
    try:
        conn = get_connection()
        if filter_type == "Today":
            wh = "WHERE DATE(end_time) = DATE('now')"
        elif filter_type == "This Week":
            wh = "WHERE DATE(end_time) >= DATE('now','-7 days')"
        elif filter_type == "This Month":
            wh = "WHERE strftime('%Y-%m', end_time) = strftime('%Y-%m','now')"
        else:
            wh = "WHERE end_time IS NOT NULL"
        query = f"SELECT COUNT(*) AS sessions, COALESCE(SUM(fee), 0) AS revenue FROM parking {wh}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.iloc[0]
    except Exception:
        import pandas as pd
        return pd.Series({"sessions": 0, "revenue": 0})
    
    
def get_full_sales_history():
    conn = get_connection()
    df = pd.read_sql_query("""
    SELECT
        s.id AS sale_id,
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

