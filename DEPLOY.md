# Deploying Baiskeli Centre POS — Where, How & Why

---

## First, understand the problem

Your app uses **SQLite** — a database that's just a file on disk.
On cloud platforms, your app runs inside a **container** (think of it as a
temporary virtual computer). When that container restarts (crash, new deploy,
platform idle timeout) — the disk resets to what it was when you last
deployed. Your SQLite file is gone. Fresh empty database.

**The solution: mount a persistent volume** — a separate disk that survives
container restarts. Your database lives there, not inside the container.
You point the app at it with one environment variable:

```
BAISKELI_DB_PATH=/data/baiskeli.db
```

---

## The honest comparison (as of 2026)

| Platform | Truly Free? | Persistent Disk | Sleeps? | Verdict |
|---|---|---|---|---|
| **Streamlit Cloud** | ✅ Free forever | ❌ No | Sometimes | ❌ Loses data on restart |
| **Railway** | 30-day trial ($5 credit), then **$5/month** | ✅ Yes (0.5GB included) | ❌ No | ✅ Best for this app |
| **Render** | ✅ Free web service | ❌ Disk is **paid add-on** ($0.25/GB) | ✅ Sleeps after 15min | ⚠️ Free = no persistent disk |
| **Fly.io** | ❌ No real free tier (killed in 2024) | ✅ Yes (paid) | ❌ No | ❌ Skip for now |
| **Your own machine / VPS** | ✅ Free if you own the machine | ✅ Yes — it's your disk | ❌ No | ✅ Best if you have a machine |

**Bottom line:**
- For a real shop: **Railway** ($5/month, clean, simple, data is safe)
- Truly zero budget: **Run it locally** on any laptop on the shop WiFi
- Render only makes sense if you pay for the disk add-on too

---

## Option 1 — Railway (Recommended — $5/month after trial)

Railway is the cleanest option for this app. You get a 30-day free trial
with $5 credits (no credit card needed for trial). After that it's $5/month.
A small bicycle shop spending $5/month for a POS system that never loses data
is a good deal.

**No new code needed. app.py doesn't change. Just connect and set one variable.**

### Steps

1. Go to [railway.app](https://railway.app) → Sign up (GitHub login works)

2. Click **New Project → Deploy from GitHub repo** → select `baiskeli`

3. Railway auto-detects the `railway.json` file and builds the app.

4. Once deployed, click your service → **Variables** tab → Add:
   ```
   BAISKELI_DB_PATH = /data/baiskeli.db
   ```

5. Go to **Volumes** tab → Click **Add Volume**:
   - Mount path: `/data`
   - Size: 1 GB (included in plan, costs nothing extra)

6. Click **Redeploy** (or it redeploys automatically).

7. Railway gives you a public URL like `baiskeli-production.railway.app` — done.

**That's literally it. No Dockerfile, no config files to write, just 7 steps.**

---

## Option 2 — Render (Free web service, but disk costs ~$1/month)

Render's free tier gives you a web service that actually runs (unlike Streamlit
Cloud). BUT — persistent disks are a **paid add-on** at $0.25/GB/month.
So "free Render" means your database still resets on restarts (every 15 mins
of inactivity the service sleeps and restarts).

If you're okay spending ~$1-2/month total, Render + disk works great.

**No new code needed. The `render.yaml` file in the repo handles everything.**

### Steps

1. Go to [render.com](https://render.com) → Sign up

2. Click **New → Web Service** → Connect GitHub → select `baiskeli`

3. Render reads `render.yaml` automatically. Review the settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

4. Under **Environment Variables**, add:
   ```
   BAISKELI_DB_PATH = /data/baiskeli.db
   ```

5. Under **Disks** (requires a paid instance):
   - Name: `baiskeli-data`
   - Mount Path: `/data`
   - Size: 1 GB

6. Deploy → Render gives you a `.onrender.com` URL.

> ⚠️ Free tier sleeps after 15 minutes of inactivity. First load after sleep
> takes ~30 seconds. Fine for occasional use, not great for a busy shop.

---

## Option 3 — Your own machine / local network (100% free forever)

This is honestly the best option if the shop has a decent laptop or an old PC
that can stay on. Staff connect from their phones or other computers over WiFi.

**Nothing changes. No cloud needed.**

### Setup

```bash
# On the shop machine (one time)
pip install -r requirements.txt

# Every time you want to start the POS
streamlit run app.py
```

Data is stored in `Databases/baiskeli.db` on that machine's disk.
It never vanishes. No monthly cost. Works offline.

### Staff access

Other devices on the same WiFi connect at:
```
http://<machine-ip>:8501
```

Find the machine IP:
- Windows: `ipconfig` → look for IPv4 Address
- Mac/Linux: `ifconfig` or `ip addr`

Something like: `http://192.168.1.5:8501`

---

## Option 4 — Docker (anywhere that runs Docker)

A `Dockerfile` is included. This works on any VPS (DigitalOcean, Hetzner,
Contabo — ~$4/month), Railway, Render, Fly.io, or your own machine.

```bash
# Build
docker build -t baiskeli-pos .

# Run with a persistent volume
docker run -d \
  -p 8501:8501 \
  -v baiskeli-data:/data \
  -e BAISKELI_DB_PATH=/data/baiskeli.db \
  --name baiskeli \
  baiskeli-pos
```

Data lives in the Docker volume `baiskeli-data`. Survives container restarts.

---

## Environment variable reference

| Variable | What it does | Example value |
|---|---|---|
| `BAISKELI_DB_PATH` | Override database location | `/data/baiskeli.db` |
| `PORT` | Port to run on (auto-set by Railway/Render) | `8501` |

---

## Backup reminder

Wherever you deploy — go to **Admin Tools → Backup & Export** regularly and
download the `.db` file. Keep a copy somewhere safe. It's your insurance.
