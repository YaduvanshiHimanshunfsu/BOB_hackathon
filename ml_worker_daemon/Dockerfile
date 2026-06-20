FROM python:3.12-slim
WORKDIR /app

# Install system dependencies required for psycopg2 and numpy if needed
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Copy shared utilities
COPY ../shared /app/shared

ENV PYTHONPATH=/app
CMD ["python", "ml_worker_daemon/worker.py"]
