# Dockerfile
# Use official Python image as base -> Porfolio_Service
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORTFOLIO_API_PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies (updated with libpq-dev)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
        postgresql-client \
        libpq-dev \
        netcat-traditional \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with legacy resolver as fallback
RUN pip install --no-cache-dir --upgrade pip \
    && (pip install --no-cache-dir -r requirements.txt || \
        pip install --no-cache-dir --use-deprecated=legacy-resolver -r requirements.txt)

# Copy application code
COPY . .

# Create a non-root user and switch to it
RUN useradd -m portfoliouser && chown -R portfoliouser:portfoliouser /app
USER portfoliouser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

## Dockerfile
## Use official Python image with slim-bullseye for better security
#FROM python:3.9-slim-bullseye as builder
#
## Set environment variables
#ENV PYTHONDONTWRITEBYTECODE=1 \
#    PYTHONUNBUFFERED=1 \
#    PIP_NO_CACHE_DIR=1 \
#    PIP_DISABLE_PIP_VERSION_CHECK=1 \
#    POETRY_VERSION=1.6.1
#
## Install system dependencies
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential \
#    libpq-dev \
#    && rm -rf /var/lib/apt/lists/*
#
## Install poetry
#RUN pip install "poetry==$POETRY_VERSION"
#
## Set work directory
#WORKDIR /app
#
## Copy only dependency files first to leverage Docker cache
#COPY pyproject.toml poetry.lock* ./
#
## Install project dependencies
#RUN poetry config virtualenvs.create false \
#    && poetry install --no-root --only main
#
## --- Runtime stage ---
#FROM python:3.9-slim-bullseye
#
## Install runtime dependencies
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    libpq5 \
#    && rm -rf /var/lib/apt/lists/*
#
## Create non-root user
#RUN useradd -m -u 1001 equityuser
#
## Set work directory and copy from builder
#WORKDIR /app
#COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
#COPY --from=builder /usr/local/bin /usr/local/bin
#COPY --chown=equityuser:equityuser . .
#
## Switch to non-root user
#USER equityuser
#
## Health check
#HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#    CMD curl -f http://localhost:8001/health || exit 1
#
## Expose the port
#EXPOSE 8001
#
## Command to run the application
#CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "4", "--threads", "2", "src.main:app"]