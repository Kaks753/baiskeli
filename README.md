# 🚴 Baiskeli Centre POS System

A full Point-of-Sale and inventory management system for a bicycle shop.
Built with Python + Streamlit + SQLite.

---

## ⚠️ Important: Where to deploy (read this first)

**Do NOT use Streamlit Cloud if you need data to survive restarts.**
Streamlit Cloud has no persistent disk — your database will vanish every time
the container restarts (which happens after inactivity or a new deploy).

**Use Railway or Render instead** — both have free tiers and give you a
persistent disk.  See **[DEPLOY.md](DEPLOY.md)** for step-by-step instructions.

---

## Features

- 🛒 **Point of Sale** — cart, discount, change calculation, M-Pesa/Cash/Card
- 📦 **Inventory** — add products, restock, low-stock alerts, full audit log
- 🔧 **Repairs** — job tracking, parts used, service cost, PDF receipt
- 🅿️ **Parking** — hourly billing, active bay view, history
- 📊 **Analytics** — revenue, profit, top products, payment breakdown
- 👥 **Multi-user** — admin vs cashier roles, bcrypt passwords, login rate-limiting
- 💾 **Backup** — one-click DB backup + Excel export of all tables

---

## Quick start (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

### Default login credentials

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin2026   |
| Cashier | cashier  | cashier2026 |

⚠️ Change these immediately after first login via **Admin Tools → Change Password**.

---

## Folder structure

```
BaiskeliPOS/
├── app.py              ← main Streamlit app
├── db_config.py        ← single source of truth for DB path + connection
├── init_db.py          ← creates tables, seeds default users
├── migration.py        ← safe additive-only schema migrations
├── schema.sql          ← table definitions
├── DEPLOY.md           ← deployment guide (Railway / Render / local)
├── requirements.txt
├── Modules/
│   ├── auth.py         ← login, users, audit logging
│   ├── analytics.py    ← sales summaries and charts
│   ├── inventory.py    ← products, stock management
│   ├── pos.py          ← checkout / sale processing
│   ├── receipt.py      ← PDF receipt generation
│   ├── repairs.py      ← repair job management
│   ├── parking.py      ← bike parking
│   └── backup.py       ← DB backup + Excel export
├── Assets/             ← place logo.png here
├── Databases/          ← auto-created, holds baiskeli.db
└── Backups/            ← auto-created, backup files land here
```

---

## Adding your logo

Place a PNG at `Assets/logo.png` (recommended 300×200 px).

---

## Customising shop details

Edit these in `Modules/receipt.py`:
```python
SHOP_NAME    = "Baiskeli Centre"
SHOP_ADDRESS = "Nairobi CBD, Kenya"
SHOP_PHONE   = "0712 345 678"
SHOP_EMAIL   = "info@baiskelicentre.co.ke"
```

---

## Database: how persistence works

The DB path is resolved in `db_config.py`:

1. If the environment variable `BAISKELI_DB_PATH` is set → use that path.
   Set this to a **persistent volume path** on Railway/Render so data survives restarts.
2. Otherwise → defaults to `<repo-root>/Databases/baiskeli.db` (absolute path,
   works perfectly for local / self-hosted installs).

```bash
# Railway / Render: set this in your environment variables
BAISKELI_DB_PATH=/data/baiskeli.db
```

---

## Adding new tables or columns (future-proofing)

### New column on an existing table
In `migration.py`, add:
```python
safe_add_column(cursor, "products", "your_new_column", "TEXT", "''")
```
Safe to run multiple times — only adds if the column doesn't exist.

### Brand new table
Add a `CREATE TABLE IF NOT EXISTS` block in `schema.sql`.
It applies automatically on the next startup.

**NEVER** drop existing tables or columns in `migration.py`.

---

## Security notes

- Passwords hashed with bcrypt (never stored plain)
- Login rate-limiting: 5 failed attempts = 5-minute lockout
- All admin actions logged in `audit_logs` table
- Cashiers cannot see cost prices or access admin tools
- Double confirmation required before any deletion

---

## Backup & Export

**Admin Tools → Backup & Export**
- Creates a timestamped `.db` copy in `Backups/`
- Excel export of all tables available for download
- Download and store backups off-server regularly
