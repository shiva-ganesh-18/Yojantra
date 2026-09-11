FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y     gcc     libpq-dev     tesseract-ocr     tesseract-ocr-hin     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# BuildKit pip cache: survives per-layer retries so flaky registries resume
# instead of re-downloading. Zero runtime effect (wheels still installed).
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

# Production startup (multi-worker, no --reload).
# Listens on Render's $PORT when present, otherwise 8001 locally.
# Local development overrides the command with --reload via docker-compose.override.yml.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001} --workers 2"]
