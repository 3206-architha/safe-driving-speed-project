FROM python:3.11-slim

WORKDIR /app

# system deps needed by psycopg2 and scientific libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# gunicorn manages multiple uvicorn workers with auto-restart on crash —
# this is what makes the process resilient for 24/7 uptime instead of
# relying on a single `uvicorn` process that dies on an unhandled error.
CMD ["gunicorn", "app.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
