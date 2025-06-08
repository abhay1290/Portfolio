# portfolio service config.py
import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


class Settings:
    SERVICE_NAME = "Portfolio Service"
    VERSION = "1.0.0"

    # Database Configuration(env var, defaults)
    DB_HOST = os.getenv("PORTFOLIO_DB_HOST", "localhost")
    DB_PORT = os.getenv("PORTFOLIO_DB_PORT", "4200")
    DB_NAME = os.getenv("PORTFOLIO_DB_NAME", "portfolio")
    DB_USER = os.getenv("PORTFOLIO_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("PORTFOLIO_DB_PASSWORD", "HippO1290")
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Redis Configuration
    REDIS_HOST = os.getenv("PORTFOLIO_REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("PORTFOLIO_REDIS_PORT", "6379")

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("PORTFOLIO_CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    CELERY_RESULT_BACKEND = os.getenv("PORTFOLIO_CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

    # API Configuration
    API_HOST = os.getenv("PORTFOLIO_API_HOST", "0.0.0.0")
    API_PORT = os.getenv("PORTFOLIO_API_PORT", "8000")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Service Discovery
    SERVICE_HOST = os.getenv("PORTFOLIO_SERVICE_NAME", "portfolio-service")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Health Check Configuration
    HEALTH_CHECK_ENDPOINT = "/health"
    METRICS_ENDPOINT = "/metrics"

    # Inter-service Communication
    SHARED_REDIS_HOST = os.getenv("SHARED_REDIS_HOST", "shared-redis")
    SHARED_REDIS_PORT = int(os.getenv("SHARED_REDIS_PORT", "6379"))
    SHARED_REDIS_URL = f"redis://{SHARED_REDIS_HOST}:{SHARED_REDIS_PORT}"

    # Portfolio Service URL (for inter-service calls)
    EXTERNAL_SERVICE_TIMEOUT = "30"
    EQUITY_SERVICE_URL = os.getenv("EQUITY_SERVICE_URL", "http://equity-service:8001")
    FIXED_INCOME_SERVICE_URL = os.getenv("FIXED_INCOME_SERVICE_URL", "http://fixed-income-service:8002")

    # # Cache Configuration
    # CACHE_TTL = int(os.getenv("PORTFOLIO_CACHE_TTL", "300"))  # 5 minutes default
    #
    # # Connection Pool Settings
    # DB_POOL_SIZE = int(os.getenv("PORTFOLIO_DB_POOL_SIZE", "10"))
    # DB_MAX_OVERFLOW = int(os.getenv("PORTFOLIO_DB_MAX_OVERFLOW", "20"))
    #
    # # Rate Limiting
    # RATE_LIMIT_REQUESTS = int(os.getenv("PORTFOLIO_RATE_LIMIT_REQUESTS", "100"))
    # RATE_LIMIT_WINDOW = int(os.getenv("PORTFOLIO_RATE_LIMIT_WINDOW", "60"))


# Instantiate the config
settings = Settings()
