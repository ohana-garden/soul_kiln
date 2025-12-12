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

# Default command
CMD ["python", "-m", "scripts.run_evolution"]
