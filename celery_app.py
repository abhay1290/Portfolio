import os
import sys

# Ensure project root (Portfolio/) is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from celery import Celery

celery_app = Celery(
    "FixedIncome",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

# Import the task module explicitly to ensure registration
import FixedIncome.tasks.analytics  # noqa

celery_app.autodiscover_tasks([
    "FixedIncome.tasks.analytics",
])
