FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    web3==6.15.1 \
    psycopg2-binary==2.9.9 \
    prometheus-client==0.19.0

# Copy indexer script
COPY indexer.py .

CMD ["python", "-u", "indexer.py"]
