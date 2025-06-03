# Dockerfile for fixed_income_service
# Use official Python image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user and switch to it
RUN useradd -m fixedincomeuser && chown -R fixedincomeuser:fixedincomeuser /app
USER fixedincomeuser

# Expose the port the app runs on (change if different from equity service)
EXPOSE 8002

# Command to run the application
CMD ["python", "src/main.py"]