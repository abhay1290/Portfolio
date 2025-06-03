# config.py
import os

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


class Settings:
    SERVICE_NAME = "Equity Service"
    VERSION = "1.0.0"

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "4200")
    DB_NAME = os.getenv("DB_NAME", "equity")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "HippO1290")
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # Redis Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")

    # Celery Configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/1")

    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = os.getenv("API_PORT", "8000")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# Instantiate the config
settings = Settings()
