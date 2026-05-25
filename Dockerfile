# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Baiskeli Centre POS
#
# This file lets you deploy on:
#   • Railway   (auto-detects Dockerfile, just connect the repo)
#   • Render    (select "Docker" as runtime when creating the service)
#   • Fly.io    (fly launch --dockerfile Dockerfile)
#   • Any VPS   (docker build + docker run)
#   • Local     (docker-compose up)
#
# PERSISTENT DATA — always mount a volume at /data and set:
#   BAISKELI_DB_PATH=/data/baiskeli.db
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install dependencies first (Docker layer caching — faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Create directories the app needs (will be overridden by volume mounts)
RUN mkdir -p /app/Databases /app/Backups /app/Assets \
    && chown -R appuser:appuser /app

USER appuser

# Expose Streamlit's default port
EXPOSE 8501

# Health check so the platform knows when the app is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start command — $PORT is injected by Railway/Render/Fly automatically.
# Falls back to 8501 if running locally.
CMD streamlit run app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
