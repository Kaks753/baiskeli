# Deploying Baiskeli Centre POS — Persistent Data Guide

## Why Streamlit Cloud loses your data

Streamlit Cloud runs your app inside a **container that resets whenever it
restarts** (after inactivity, a new deploy, or a platform cycle).  Your SQLite
database is a file inside that container.  When the container resets, the file
is gone — fresh empty database every time.

**The fix is simple: host somewhere that gives you a persistent disk.**

---

## Option 1 — Railway (recommended, free tier available)

Railway mounts a real disk that survives restarts.

### Steps

1. **Sign up** at [railway.app](https://railway.app) and create a new project.

2. **Add a volume** — in your project dashboard:
   - Click **+ New** → **Volume**
   - Mount path: `/data`
   - This folder survives container restarts forever.

3. **Deploy the repo** — click **+ New** → **GitHub Repo** → select `baiskeli`.

4. **Set the environment variable** — in your service's **Variables** tab:
   ```
   BAISKELI_DB_PATH = /data/baiskeli.db
   ```
   The app reads this at startup and stores the database on the persistent volume.

5. **Set the start command** — in Settings → Deploy:
   ```
   streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

6. Done — Railway gives you a public URL and your data lives on.

---

## Option 2 — Render (also free tier)

1. Sign up at [render.com](https://render.com).
2. **New Web Service** → connect GitHub → select `baiskeli`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. **Add a Persistent Disk** under the service settings:
   - Mount path: `/data`
   - Size: 1 GB (free tier)
6. **Add Environment Variable**:
   ```
   BAISKELI_DB_PATH = /data/baiskeli.db
   ```

---

## Option 3 — Self-hosted / local network (simplest)

Run it on a laptop or a Raspberry Pi on the shop's WiFi.  Staff connect over
the local network.  No cloud needed, data lives on the machine's disk.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Access on other devices at `http://<machine-ip>:8501`.

---

## Option 4 — Streamlit Cloud (data will not persist between restarts)

Streamlit Cloud has no persistent disk.  **Do not use it if you need data
to survive restarts.**  It is fine for demos but not for a real shop.

If you absolutely must use Streamlit Cloud, add the following to
`.streamlit/secrets.toml` and mount external storage yourself:
```toml
[env]
BAISKELI_DB_PATH = "/mount/your-external-volume/baiskeli.db"
```

---

## Backup reminder

Regardless of where you deploy, go to **Admin Tools → Backup & Export**
regularly and download the `.db` file.  It's your safety net.
