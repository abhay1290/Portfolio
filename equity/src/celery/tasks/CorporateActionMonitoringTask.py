import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict

from celery import Task
from sqlalchemy import and_
from sqlalchemy.orm import Session

from equity.src.celery.app import celery_app
from equity.src.celery.tasks.CorporateActionTask import batch_process_eod_actions
from equity.src.database import SessionLocal
from equity.src.model.corporate_actions.enums.StatusEnum import StatusEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase

logger = logging.getLogger(__name__)


class MonitoringTask(Task):
    """Base task class for monitoring tasks"""

    _session = None

    def get_session(self) -> Session:
        if not self._session:
            self._session = SessionLocal()
        return self._session

    def after_return(self, *args, **kwargs):
        if self._session:
            self._session.close()


# Monitoring and maintenance tasks
@celery_app.task(bind=True, base=MonitoringTask, name='corporate_actions.monitor_failed_actions')
def monitor_failed_actions(self) -> Dict[str, Any]:
    """Monitor and report failed corporate actions"""
    session = self.get_session()
    try:

        cutoff = datetime.now() - timedelta(hours=1)
        failures = session.query(CorporateActionBase).filter(
            StatusEnum.FAILED == CorporateActionBase.status,
            CorporateActionBase.updated_at >= cutoff
        ).all()

        if failures:
            logger.warning("Detected failed corporate actions", extra={
                'count': len(failures),
                'action_ids': [f.id for f in failures]
            })
            # Here you would add actual notification logic
            return {
                'status': 'completed',
                'failure_count': len(failures),
                'action_ids': [f.id for f in failures]
            }
        return {'status': 'no_failures'}

    except Exception:
        logger.error("Failed to monitor actions", exc_info=True)
        raise


@celery_app.task(bind=True, base=MonitoringTask, name='corporate_actions.cleanup_completed_tasks')
def cleanup_completed_tasks(session: Session, days_to_keep: int = 7):
    """Cleanup old completed task records"""
    try:
        from datetime import timedelta
        from sqlalchemy import and_

        cutoff = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = session.query(CorporateActionBase).filter(
            and_(
                CorporateActionBase.status.in_([StatusEnum.CLOSED, StatusEnum.FAILED]),
                CorporateActionBase.updated_at < cutoff
            )
        ).delete(synchronize_session=False)
        session.commit()

        logger.info("Cleaned up completed tasks", extra={
            'deleted_count': deleted_count,
            'cutoff_date': cutoff.isoformat()
        })
        return {
            'status': 'completed',
            'deleted_count': deleted_count
        }

    except Exception:
        session.rollback()
        logger.error("Failed to cleanup tasks", exc_info=True)
        raise


@celery_app.task(bind=True, base=MonitoringTask, name='corporate_actions.process_overdue_actions')
def process_overdue_actions(session: Session):
    """Process actions that missed their scheduled window"""
    try:
        overdue_actions = session.query(CorporateActionBase).filter(
            and_(
                CorporateActionBase.execution_date < date.today(),
                CorporateActionBase.status == StatusEnum.PENDING
            )
        ).all()

        if not overdue_actions:
            return {'status': 'no_overdue_actions'}

        logger.warning("Processing overdue corporate actions", extra={
            'count': len(overdue_actions)
        })

        # Reuse batch processing logic but with specific filtering
        return batch_process_eod_actions(target_date=date.today().isoformat())

    except Exception:
        logger.error("Failed to process overdue actions", exc_info=True)
        raise
