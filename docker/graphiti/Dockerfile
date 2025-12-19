FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    graphiti-core[falkordb,anthropic]>=0.5.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.23.0 \
    pydantic>=2.0.0

# Copy server code
COPY graphiti_server.py .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run server
CMD ["uvicorn", "graphiti_server:app", "--host", "0.0.0.0", "--port", "8000"]
