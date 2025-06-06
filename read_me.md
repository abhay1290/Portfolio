                  # Financial Services Microservices

A complete microservices architecture for financial services with Equity, Fixed Income, and Portfolio services, where the Portfolio service acts as the primary access point for client operations.

## Architecture Overview
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Equity Service │    │Fixed Income Svc │    │  Portfolio Svc  │    │  Shared Redis   │
│   (Port 8001)   │    │   (Port 8002)   │    │   (Port 8000)   │    │   (Port 6381)   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │                      │
         │                      │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐             │
│  Equity Postgres│    │ FI Postgres DB  │    │ Portfolio PG DB │             │
│   (Port 5432)   │    │   (Port 5433)   │    │   (Port 5434)   │             │
└─────────────────┘    └─────────────────┘    └─────────────────┘             │
         │                      │                      │                      │
         │                      │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐             │
│  Equity Redis   │    │   FI Redis      │    │ Portfolio Redis │◄───────────-┘
│   (Port 6379)   │    │   (Port 6380)   │    │   (Port 6382)   │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         │                      │                      │
┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐
│Equity Celery Wkr│    │ FI Celery Wkr   │    │Portfolio Celery │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                      ▲                      ▲
         └──────────┬──────────┘                      │
                    │                                 │
                    └─────────────────────────────────┘
## Services

### 1. Portfolio Service (Primary Access Point)
- **Port**: 8000 (main client-facing port)
- **Database**: portfolio-postgres (Port 5434)
- **Redis**: portfolio-redis (Port 6382)
- **Celery Worker**: portfolio-celery-worker
- **Dependencies**: Equity Service, Fixed Income Service, Shared Redis
- **Role**: 
  - Main entry point for client applications
  - Orchestrates interactions between equity and fixed income services
  - Manages portfolio composition and calculations

### 2. Equity Service
- **Port**: 8001
- **Database**: equity-postgres (Port 5432)
- **Redis**: equity-redis (Port 6379)
- **Celery Worker**: equity-celery-worker

### 3. Fixed Income Service
- **Port**: 8002
- **Database**: fixed-income-postgres (Port 5433)
- **Redis**: fixed-income-redis (Port 6380)
- **Celery Worker**: fixed-income-celery-worker

### 4. Shared Services
- **Shared Redis**: For inter-service communication (Port 6381)
- **pgAdmin**: Database management (Port 8080)
- **Redis Commander**: Redis management (Port 8081)```

## Project Structure

financial-services/
├── .env # Project environment variables
├── docker-compose.yml # Docker Compose configuration
├── Makefile # Project management commands
├── README.md # This file
├── requirements.txt # Python dependencies
├── scripts/
│ ├── entrypoint.sh # Service entrypoint script
│ ├── init-equity-db.sql # Equity database initialization
│ ├── init-fixed-income-db.sql # Fixed Income database initialization
│ └── init-portfolio-db.sql # Portfolio database initialization
├── equity_service/
│ ├── config.py # Equity service configuration
│ ├── Dockerfile # Equity service Docker configuration
│ ├── main.py # Equity service main application
│ ├── requirements.txt # Equity service dependencies
│ └── logs/ # Equity service logs
├── fixed_income_service/
│ ├── config.py # Fixed Income service configuration
│ ├── Dockerfile # Fixed Income service Docker configuration
│ ├── main.py # Fixed Income service main application
│ ├── requirements.txt # Fixed Income service dependencies
│ └── logs/ # Fixed Income service logs
└── portfolio_service/
├── config.py # Portfolio service configuration
├── Dockerfile # Portfolio service Docker configuration
├── main.py # Portfolio service main application
├── requirements.txt # Portfolio service dependencies
└── logs/ # Portfolio service logs## Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd financial-services
```

### 2. Environment Configuration
Copy the provided `.env` file to your project root. All necessary environment variables are pre-configured.

### 3. Start All Services
```bash
# Using Make (recommended)
make up-build

# Or using Docker Compose directly
docker-compose up -d --build
```

### 4. Verify Services
```bash
# Check service status
make status

# Check health endpoints
make health

# View logs
make logs
```


## Service Endpoints

### Portfolio Service (Primary Access Point)
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Key Endpoints**:
  - `POST /portfolios`: Create new portfolio
  - `GET /portfolios/{id}`: Get portfolio details
  - `POST /portfolios/{id}/calculate`: Calculate portfolio metrics
  - `GET /portfolios/{id}/constituents`: Get portfolio constituents
  - `POST /portfolios/{id}/rebalance`: Rebalance portfolio
  - `GET /portfolios/{id}/performance`: Get performance metrics

### Equity Service
- **API**: http://localhost:8001
- **Health Check**: http://localhost:8001/health
- **Metrics**: http://localhost:8001/metrics

### Fixed Income Service
- **API**: http://localhost:8002
- **Health Check**: http://localhost:8002/health
- **Metrics**: http://localhost:8002/metrics

## Portfolio Service Features

1. **Client-Facing Operations**:
   - Single entry point for all portfolio-related operations
   - Unified API for both equity and fixed income constituents
   - Simplified client authentication and authorization

2. **Portfolio Management**:
   - Create and manage portfolios with mixed asset classes
   - Weight allocation and rebalancing
   - Constituent addition/removal

3. **Calculations & Analytics**:
   - Portfolio valuation aggregating equity and FI components
   - Risk metrics calculation
   - Performance attribution across asset classes
   - Yield-to-maturity and duration calculations

4. **Dependency Coordination**:
   - Orchestrates calls to Equity and Fixed Income services
   - Caches frequently accessed data from underlying services
   - Manages consistency across services

[Rest of the original content remains unchanged, maintaining all existing commands, configuration details, and other sections]
### Management Interfaces
- **pgAdmin**: http://localhost:8080 (admin@example.com / admin)
- **Redis Commander**: http://localhost:8081

## Development Commands

### Using Make
```bash
# Build services
make build

# Start services
make up

# Stop services
make down

# Restart services
make restart

# View logs
make logs
make logs-equity    # Equity service only
make logs-fi        # Fixed Income service only

# Check status
make status

# Health check
make health

# Run tests
make test

# Database migrations
make db-migrate

# Access service shells
make shell-equity
make shell-fi

# Clean up
make clean
```

### Using Docker Compose Directly
```bash
# Build and start
docker-compose up -d --build

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

## Configuration

### Environment Variables
All configuration is managed through environment variables in the `.env` file:

- **Service Ports**: EQUITY_API_PORT, FIXED_INCOME_API_PORT
- **Database Settings**: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD (per service)
- **Redis Settings**: REDIS_HOST, REDIS_PORT (per service)
- **Celery Settings**: CELERY_BROKER_URL, CELERY_RESULT_BACKEND (per service)

### Inter-Service Communication
Services can communicate through:
1. **HTTP APIs**: Direct service-to-service HTTP calls
2. **Shared Redis**: For pub/sub messaging and shared caching
3. **Message Queues**: Through Celery for async processing

## Database Management

### Migrations
```bash
# Run migrations for both services
make db-migrate

# Or individually
docker-compose exec equity-service alembic upgrade head
docker-compose exec fixed-income-service alembic upgrade head
```

### Backups
```bash
# Create backups
make backup
```

### Access Databases
```bash
# Using pgAdmin web interface
# Visit http://localhost:8080

# Or directly via psql
docker-compose exec equity-postgres psql -U equity_user -d equity_db
docker-compose exec fixed-income-postgres psql -U fixed_income_user -d fixed_income_db
```

## Monitoring and Logging

### Logs
- Service logs are mounted to `./[service]/logs/` directories
- Use `make logs` or `docker-compose logs -f` to view real-time logs

### Health Checks
- All services include health check endpoints
- Docker health checks are configured for automatic monitoring
- Use `make health` to check all service health

### Scaling
```bash
# Scale specific services
make scale-equity    # Scale equity service and workers
make scale-fi        # Scale fixed income service and workers

# Or manually
docker-compose up -d --scale equity-service=2 --scale equity-celery-worker=2
```

## Testing

### Run Tests
```bash
# Run all tests
make test

# Run tests for specific service
docker-compose exec equity-service python -m pytest tests/ -v
docker-compose exec fixed-income-service python -m pytest tests/ -v
```

## Security Considerations

1. **Database Credentials**: Use strong passwords and consider using Docker secrets in production
2. **Network Isolation**: Services communicate through a dedicated Docker network
3. **Non-Root Users**: All services run as non-root users inside containers
4. **Health Checks**: Automated health monitoring for all services

## Production Deployment

For production deployment:

1. **Environment Variables**: Use secure credential management
2. **Volumes**: Configure persistent volumes for data
3. **Load Balancing**: Add load balancers in front of services
4. **Monitoring**: Integrate with monitoring solutions (Prometheus, Grafana)
5. **Logging**: Configure centralized logging (ELK stack, Fluentd)

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 8001, 8002, 5432, 5433, 6379, 6380, 6381 are available
2. **Database Connection**: Check if databases are healthy using `make status`
3. **Redis Connection**: Verify Redis instances are running and accessible
4. **Service Dependencies**: Services wait for dependencies to be ready via health checks

### Debug Commands
```bash
# Check service status
make status

# View detailed logs
make logs

# Access service shells for debugging
make shell-equity
make shell-fi

# Check health endpoints
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Contributing

1. Follow the existing code structure and naming conventions
2. Add tests for new features
3. Update documentation for any configuration changes
4. Use the provided linting and formatting tools (black, isort, flake8)

## License

[Your License Here]