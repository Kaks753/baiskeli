-- ============================================================
-- BAISKELI CENTRE - DATABASE SCHEMA
-- ============================================================
-- HOW TO ADD NEW TABLES/COLUMNS IN FUTURE:
-- 1. Add new CREATE TABLE IF NOT EXISTS blocks below
-- 2. Add new ALTER TABLE lines in migration.py
-- 3. NEVER drop existing tables — always use IF NOT EXISTS
-- ============================================================

-- PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,        -- bike, accessory, service, parking
    subcategory TEXT,              -- kids, adult, repair, etc.
    size TEXT,                   -- for bikes
    brand TEXT,                  -- for future use
    description TEXT,            -- for future use
    cost_price REAL,
    selling_price REAL NOT NULL,
    quantity_in_stock INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- SALES TABLE
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_amount REAL NOT NULL,
    payment_method TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT DEFAULT 'sale',  -- sale, service, parking
    reference_id INTEGER,  -- for linking to service or parking if needed
    customer_name TEXT DEFAULT 'Walk-in',
    discount REAL DEFAULT 0,
    amount_paid REAL
);

-- SALE ITEMS (what was sold in each sale)
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (sale_id) REFERENCES sales(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- INVENTORY LOGS (CRITICAL for tracking stock history)
CREATE TABLE IF NOT EXISTS inventory_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    change INTEGER,  -- +10, -2 etc
    reason TEXT,     -- sale, restock, adjustment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- CUSTOMERS (for future invoices + loyalty)
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SERVICES (repairs, maintenance)
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT,
    price REAL
);


-- PARKING (for commuters)
CREATE TABLE IF NOT EXISTS parking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    bike_description TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    fee REAL
);

CREATE TABLE IF NOT EXISTS repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    bike_type TEXT,
    issue TEXT,
    service_cost REAL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repair_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (repair_id) REFERENCES repairs(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);


-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

-- AUDIT LOGS (track all sensitive actions)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);