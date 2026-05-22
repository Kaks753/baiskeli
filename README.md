# 🚴 Baiskeli Centre POS System

## Setup Instructions

### 1. Prerequisites
- Python 3.9 or newer
- pip

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Folder Structure Required
```
BaiskeliPOS/
├── app.py
├── init_db.py
├── migration.py
├── schema.sql
├── requirements.txt
├── Modules/
│   ├── __init__.py
│   ├── auth.py
│   ├── analytics.py
│   ├── inventory.py
│   ├── pos.py
│   ├── receipt.py
│   ├── repairs.py
│   ├── parking.py
│   └── backup.py
├── Assets/
│   └── logo.png        ← Place your shop logo here
├── Databases/          ← Auto-created
└── Backups/            ← Auto-created
```

### 4. Add Your Logo
Place your shop logo at `Assets/logo.png`.
Recommended size: 300×200 pixels, PNG format.

### 5. Customise Shop Details
Edit these lines in `Modules/receipt.py`:
```python
SHOP_NAME    = "Baiskeli Centre"
SHOP_ADDRESS = "Nairobi CBD, Kenya"
SHOP_PHONE   = "0712 345 678"
SHOP_EMAIL   = "info@baiskelicentre.co.ke"
```

### 6. Run the App
```bash
streamlit run app.py
```

The app opens in your browser at http://localhost:8501

---

## Default Credentials
| Role    | Username | Password      |
|---------|----------|---------------|
| Admin   | admin    | admin2026     |
| Cashier | cashier  | cashier2026   |

⚠️ **Change default passwords immediately after first login!**

---

## Adding New Database Tables/Columns (Future-Proofing)

### Adding a New Column to an Existing Table
In `migration.py`, add:
```python
safe_add_column(cursor, "products", "your_new_column", "TEXT", "''")
```
This is **safe** — it only adds if the column doesn't already exist.

### Adding a Brand New Table
In `schema.sql`, add a new `CREATE TABLE IF NOT EXISTS` block.
Then run the app — it will apply automatically on next startup.

**NEVER** drop existing tables or columns in migration.py.

---

## Security Notes
- Bcrypt password hashing
- Login rate-limiting: 5 failed attempts = 5-minute lockout  
- All admin actions are logged in `audit_logs` table
- Cashiers cannot see cost prices
- Only admins can export data, delete sales/products
- Double confirmation required for all deletions

---

## Backup & Export
- **Admin Tools → Backup & Export** to create DB backups
- Backups stored in `Backups/` folder
- Excel export of all tables available
- Only admins can access these features

---

## Discount & Checkout
At checkout, staff can:
1. Enter a discount amount (KES)
2. Enter the actual amount the customer paid
3. System shows change to give back
4. All discounts are recorded for analytics
