#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting Equity Service Initialization..."

# ======================
# UTILITY FUNCTIONS
# ======================

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    local host=$1
    local port=$2
    local user=$3
    local db=$4
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for PostgreSQL at $host:$port (database: $db)..."

    while [ $attempt -le $max_attempts ]; do
        if pg_isready -h "$host" -p "$port" -U "$user" -d "$db" >/dev/null 2>&1; then
            echo "✅ PostgreSQL is ready!"
            return 0
        fi

        echo "⏳ Attempt $attempt/$max_attempts: PostgreSQL not ready, waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "❌ PostgreSQL failed to become ready after $max_attempts attempts"
    exit 1
}

# Function to wait for Redis to be ready
wait_for_redis() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $service_name Redis at $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if redis-cli -h "$host" -p "$port" ping >/dev/null 2>&1; then
            echo "✅ $service_name Redis is ready!"
            return 0
        fi

        echo "⏳ Attempt $attempt/$max_attempts: $service_name Redis not ready, waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "❌ $service_name Redis failed to become ready after $max_attempts attempts"
    exit 1
}

# Function to test database connection with actual query
test_database_connection() {
    local host=$1
    local port=$2
    local user=$3
    local db=$4
    local password=$5

    echo "🔍 Testing database connection with actual query..."

    export PGPASSWORD="$password"
    if psql -h "$host" -p "$port" -U "$user" -d "$db" -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✅ Database connection test successful!"
        unset PGPASSWORD
        return 0
    else
        echo "❌ Database connection test failed!"
        unset PGPASSWORD
        exit 1
    fi
}

# Function to test Redis connection
test_redis_connection() {
    local host=$1
    local port=$2
    local service_name=$3

    echo "🔍 Testing $service_name Redis connection..."

    if redis-cli -h "$host" -p "$port" set "test_key_$$" "test_value" >/dev/null 2>&1 && \
       redis-cli -h "$host" -p "$port" get "test_key_$$" >/dev/null 2>&1 && \
       redis-cli -h "$host" -p "$port" del "test_key_$$" >/dev/null 2>&1; then
        echo "✅ $service_name Redis connection test successful!"
        return 0
    else
        echo "❌ $service_name Redis connection test failed!"
        exit 1
    fi
}

# Function to run database migrations
run_migrations() {
    echo "🔄 Checking for database migrations..."

    if [ -f "alembic.ini" ]; then
        echo "📋 Found alembic.ini, running database migrations..."

        # Check current migration status
        echo "🔍 Current migration status:"
        alembic current

        # Run migrations
        echo "⬆️ Running migrations..."
        alembic upgrade head

        # Verify migrations
        echo "✅ Migration completed. Current status:"
        alembic current
    else
        echo "ℹ️ No alembic.ini found, skipping database migrations"
    fi
}

# Function to create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."

    # Create logs directory
    mkdir -p /app/logs

    # Create any other necessary directories
    mkdir -p /app/tmp
    mkdir -p /app/uploads

    # Set proper permissions (we're running as appuser)
    if [ "$(id -u)" = "0" ]; then
        # If running as root, change ownership
        chown -R appuser:appuser /app/logs /app/tmp /app/uploads
    fi

    echo "✅ Directories created successfully"
}

# Function to validate environment variables
validate_environment() {
    echo "🔍 Validating environment variables..."

    local required_vars=(
        "EQUITY_DB_HOST"
        "EQUITY_DB_PORT"
        "EQUITY_DB_NAME"
        "EQUITY_DB_USER"
        "EQUITY_DB_PASSWORD"
        "EQUITY_REDIS_HOST"
        "EQUITY_REDIS_PORT"
        "EQUITY_API_HOST"
        "EQUITY_API_PORT"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ Missing required environment variables:"
        printf '  - %s\n' "${missing_vars[@]}"
        exit 1
    fi

    echo "✅ All required environment variables are set"
}

# Function to display service information
display_service_info() {
    echo ""
    echo "🏷️ ====== EQUITY SERVICE CONFIGURATION ======"
    echo "Service Name: Equity Service"
    echo "API Host: $EQUITY_API_HOST"
    echo "API Port: $EQUITY_API_PORT"
    echo "Database: $EQUITY_DB_HOST:$EQUITY_DB_PORT/$EQUITY_DB_NAME"
    echo "Redis: $EQUITY_REDIS_HOST:$EQUITY_REDIS_PORT"
    echo "Debug Mode: ${DEBUG:-false}"
    echo "Log Level: ${LOG_LEVEL:-INFO}"
    echo "=============================================="
    echo ""
}

# ======================
# MAIN INITIALIZATION
# ======================

echo "🔧 Equity Service Entrypoint Script Starting..."

# Validate environment variables first
validate_environment

# Display service configuration
display_service_info

# Create necessary directories
create_directories

# Wait for and test database
wait_for_postgres "$EQUITY_DB_HOST" "$EQUITY_DB_PORT" "$EQUITY_DB_USER" "$EQUITY_DB_NAME"
test_database_connection "$EQUITY_DB_HOST" "$EQUITY_DB_PORT" "$EQUITY_DB_USER" "$EQUITY_DB_NAME" "$EQUITY_DB_PASSWORD"

# Wait for and test equity-specific Redis
wait_for_redis "$EQUITY_REDIS_HOST" "$EQUITY_REDIS_PORT" "Equity"
test_redis_connection "$EQUITY_REDIS_HOST" "$EQUITY_REDIS_PORT" "Equity"

# Wait for shared Redis if configured
if [ -n "$SHARED_REDIS_HOST" ] && [ -n "$SHARED_REDIS_PORT" ]; then
    wait_for_redis "$SHARED_REDIS_HOST" "$SHARED_REDIS_PORT" "Shared"
    test_redis_connection "$SHARED_REDIS_HOST" "$SHARED_REDIS_PORT" "Shared"
fi

# Run database migrations
run_migrations

# Additional service-specific initialization
echo "🔧 Running Equity Service specific initialization..."

# Initialize cache if needed
if [ "$EQUITY_CACHE_WARMUP" = "true" ]; then
    echo "♻️ Warming up cache..."
    # Add cache warming logic here
    python -c "
import redis
r = redis.Redis(host='$EQUITY_REDIS_HOST', port=$EQUITY_REDIS_PORT, db=0)
r.set('service_status', 'initialized')
print('Cache warmed up successfully')
"
fi

# Create initial database data if needed
if [ "$CREATE_SAMPLE_DATA" = "true" ]; then
    echo "📊 Creating sample data..."
    # Add sample data creation logic here
    python -c "
print('Sample data creation would go here')
# Add your sample data creation logic
"
fi

echo ""
echo "🎉 ====== EQUITY SERVICE READY ======"
echo "✅ All dependencies are healthy"
echo "✅ Database migrations completed"
echo "✅ Service initialization completed"
echo "🚀 Starting Equity Service application..."
echo "======================================"
echo ""

# Execute the main command passed to the container
exec "$@"