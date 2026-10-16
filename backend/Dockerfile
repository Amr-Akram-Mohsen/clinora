FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency spec first for layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application source
COPY . .

# Non-root user for security
RUN useradd -m -u 1001 clinora && chown -R clinora:clinora /app
USER clinora

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
