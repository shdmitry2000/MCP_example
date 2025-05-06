FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_MODE=remote
ENV PORT=8000
ENV MCP_SERVER_URL=http://0.0.0.0:${PORT}
ENV MCP_SECRET_KEY=development_secret_key_123

# Expose the port
EXPOSE ${PORT}

# Run the server with explicit host and port
CMD ["sh", "-c", "python -m server.server --host 0.0.0.0 --port ${PORT:-8000} --mode remote"] 