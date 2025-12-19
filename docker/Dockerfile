FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/
COPY config/ config/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create output directory
RUN mkdir -p /app/output

# Expose port for API server
EXPOSE 8080

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Default command - start API server for Railway
# Use PORT env var which Railway provides
CMD ["python", "-m", "src.main", "serve"]
