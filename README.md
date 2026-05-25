# 🚴 Baiskeli Centre POS System

A full Point-of-Sale and inventory management system for a bicycle shop.
Built with Python + Streamlit + SQLite. No internet required for local use.

---

## ⚠️ Deployment — read this before going live

**Streamlit Cloud will lose your data.** It has no persistent disk — every
container restart wipes the database. Don't use it for a real shop.

**Best options (see [DEPLOY.md](DEPLOY.md) for full step-by-step):**

| What | Cost | Data safe? |
|---|---|---|
| Local machine on shop WiFi | Free | ✅ Always |
| Railway | $5/month (30-day free trial) | ✅ Always |
| Render + disk | ~$1-2/month | ✅ With paid disk |
| Streamlit Cloud | Free | ❌ Resets on restart |

---

## Features

- 🛒 **Point of Sale** — cart, discounts, change calculation, M-Pesa/Cash/Card
- 📦 **Inventory** — add/edit products, restock, low-stock alerts, full audit log
- 🔧 **Repairs** — job tracking, parts used, service cost, PDF receipt
- 🅿️ **Parking** — hourly billing, active bays view, history
- 📊 **Analytics** — revenue, profit, top products, payment breakdown
- 👥 **Multi-user** — admin vs cashier roles, bcrypt passwords, login rate-limiting
- 💾 **Backup** — one-click DB backup + Excel export of all tables

---

## Run locally (quickest way to get started)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

### Default credentials

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin2026   |
| Cashier | cashier  | cashier2026 |

⚠️ Change these immediately — **Admin Tools → Change Password**

---

## Project structure

```
BaiskeliPOS/
├── app.py              ← main Streamlit app (don't rename this)
├── db_config.py        ← database path + connection (WAL mode, timeouts)
├── init_db.py          ← creates tables, seeds default users
├── migration.py        ← safe additive-only schema migrations
├── schema.sql          ← table definitions
├── Dockerfile          ← deploy anywhere that runs Docker
├── railway.json        ← Railway deployment config
├── render.yaml         ← Render deployment config
├── DEPLOY.md           ← full deployment guide
├── requirements.txt
├── Modules/
│   ├── auth.py         ← login, users, audit logging
│   ├── analytics.py    ← sales summaries and charts
│   ├── inventory.py    ← products and stock management
│   ├── pos.py          ← checkout and sale processing
│   ├── receipt.py      ← PDF receipt generation
│   ├── repairs.py      ← repair job management
│   ├── parking.py      ← bike parking
│   └── backup.py       ← DB backup and Excel export
├── Assets/             ← place logo.png here
├── Databases/          ← auto-created, holds baiskeli.db
└── Backups/            ← auto-created, backup files land here
```

---

## Customising shop details

Edit `Modules/receipt.py`:
```python
SHOP_NAME    = "Baiskeli Centre"
SHOP_ADDRESS = "Nairobi CBD, Kenya"
SHOP_PHONE   = "0712 345 678"
SHOP_EMAIL   = "info@baiskelicentre.co.ke"
```

---

## How data persistence works

`db_config.py` resolves the database path:

1. If `BAISKELI_DB_PATH` env variable is set → use that (set this on Railway/Render to a persistent volume path)
2. Otherwise → defaults to `Databases/baiskeli.db` relative to the repo root — absolute path, always correct

```bash
# Set this on your deployment platform
BAISKELI_DB_PATH=/data/baiskeli.db
```

---

## Adding new columns or tables

**New column on existing table** — add to `migration.py`:
```python
safe_add_column(cursor, "products", "your_column", "TEXT", "''")
```

**New table** — add `CREATE TABLE IF NOT EXISTS` block to `schema.sql`.
Applies automatically on next startup. Never drop existing tables.

---

## Security

- Passwords hashed with bcrypt
- Login rate-limiting: 5 failed attempts = 5-minute lockout
- All admin actions logged in `audit_logs`
- Cashiers cannot see cost prices or access admin tools
- Double confirmation before any deletion
