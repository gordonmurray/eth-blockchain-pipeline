FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    web3==6.15.1

# Copy simulator script
COPY simulator.py .

CMD ["python", "-u", "simulator.py"]
