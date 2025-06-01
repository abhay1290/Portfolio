# # Ensure project root (Portfolio/) is in sys.path
# project_root = os.path.dirname(os.path.abspath(__file__))
# sys.path.insert(0, project_root)
#
# from celery import Celery
#
# celery_app = Celery(
#     "FixedIncome",
#     broker="redis://localhost:6379/0",
#     backend="redis://localhost:6379/1",
# )
#
# # Import the task module explicitly to ensure registration
# import FixedIncome.tasks.analytics  # noqa
#
# celery_app.autodiscover_tasks([
#     "FixedIncome.tasks.analytics",
# ])
import logging
import os

# celery_config.py
from celery import Celery
from celery.schedules import crontab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery('corporate_actions')

# Redis configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

celery_app.conf.update(
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
        'fanout_prefix': True,
        'fanout_patterns': True,
    },
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Reliability settings
    task_reject_on_worker_lost=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,

    # Monitoring
    worker_send_task_events=True,
    event_queue_expires=60,

    # Result expiration
    result_expires=3600,  # 1 hour

    # Security
    redis_socket_keepalive=True,
    redis_socket_timeout=30,

    # Task routing
    task_routes={
        'corporate_actions.tasks.process_corporate_action': {
            'queue': 'ca_processing',
            'routing_key': 'ca.processing'
        },
        'corporate_actions.tasks.batch_process_eod_actions': {
            'queue': 'ca_batch',
            'routing_key': 'ca.batch'
        },
        'corporate_actions.tasks.rollback_corporate_action': {
            'queue': 'ca_rollback',
            'routing_key': 'ca.rollback'
        },
        'corporate_actions.tasks.monitor_failed_actions': {
            'queue': 'ca_monitoring',
            'routing_key': 'ca.monitoring'
        },
    },

    # Beat schedule for periodic tasks
    beat_schedule={
        'process-eod-corporate-actions': {
            'task': 'corporate_actions.tasks.batch_process_eod_actions',
            'schedule': crontab(hour=18, minute=0),  # 6 PM daily
            'options': {
                'queue': 'ca_batch',
                'routing_key': 'ca.batch.eod',
                'priority': 9,  # Highest priority
            }
        },
        'monitor-failed-actions': {
            'task': 'corporate_actions.tasks.monitor_failed_actions',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
            'options': {
                'queue': 'ca_monitoring',
                'routing_key': 'ca.monitoring.failed',
                'priority': 5,
            }
        },
        'cleanup-completed-tasks': {
            'task': 'corporate_actions.tasks.cleanup_completed_tasks',
            'schedule': crontab(hour=1, minute=0),  # 1 AM daily
            'options': {
                'queue': 'ca_monitoring',
                'routing_key': 'ca.monitoring.cleanup',
                'priority': 3,
            }
        },
        'process-overdue-actions': {
            'task': 'corporate_actions.tasks.process_overdue_actions',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
            'options': {
                'queue': 'ca_batch',
                'routing_key': 'ca.batch.overdue',
                'priority': 7,
            }
        },
    },
)
