FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y     gcc     libpq-dev     tesseract-ocr     tesseract-ocr-hin     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# BuildKit pip cache: survives per-layer retries so flaky registries resume
# instead of re-downloading. Zero runtime effect (wheels still installed).
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

# Production startup configuration (multi-worker, no --reload).
# Local development overrides the command with --reload via docker-compose.override.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
