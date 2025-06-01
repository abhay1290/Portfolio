import logging
from datetime import date, datetime
from itertools import islice
from typing import Any, Dict, List, Optional

import sqlalchemy
from celery import Task, group
from sqlalchemy import and_
from sqlalchemy.orm import Session

from Equities.corporate_actions.analytics.CorporateActionExecutionEngine import ca_execution_engine
from Equities.corporate_actions.enums.PriorityEnum import PriorityEnum
from Equities.corporate_actions.enums.StatusEnum import StatusEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.database import SessionLocal
from Equities.utils.Exceptions import CorporateActionError, CorporateActionValidationError, ProcessingLockError
from celery_app import celery_app

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Enhanced base task class with database session management and connection pooling"""

    _session_pool = None
    _pool_size = 5  # Adjust based on expected concurrency

    @classmethod
    def initialize_pool(cls):
        """Initialize the connection pool"""
        if cls._session_pool is None:
            cls._session_pool = [SessionLocal() for _ in range(cls._pool_size)]

    def __init__(self):
        super().__init__()
        if DatabaseTask._session_pool is None:
            DatabaseTask.initialize_pool()
        self._session = None

    def get_session(self):
        """Get a session from the pool"""
        if self._session is None:
            self._session = DatabaseTask._session_pool.pop()
        return self._session

    def release_session(self):
        """Release the session back to the pool"""
        if self._session is not None:
            DatabaseTask._session_pool.append(self._session)
            self._session = None

    def __call__(self, *args, **kwargs):
        """Execute task with improved session management"""
        session = self.get_session()
        try:
            result = self.run_with_session(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as exc:
            session.rollback()
            logger.error(f"Task {self.name} failed: {str(exc)}", exc_info=True)
            raise
        finally:
            self.release_session()

    def on_failure(self, exc, task_id, args, kwargs, info):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {str(exc)}")
        super().on_failure(exc, task_id, args, kwargs, info)

    def run_with_session(self, session: Session, *args, **kwargs):
        """Override this method instead of run() for database tasks"""
        raise NotImplementedError("Subclasses must implement run_with_session")


@celery_app.task(bind=True, base=DatabaseTask, name='corporate_actions.tasks.process_corporate_action')
def process_corporate_action(self, session: Session, corporate_action_id: int,
                             force_execution: bool = False) -> Dict[str, Any]:
    """Process a single corporate action with enhanced error handling and validation"""

    logger.info(f"Processing corporate action {corporate_action_id}", extra={
        'corporate_action_id': corporate_action_id,
        'force_execution': force_execution
    })

    ca = None
    try:
        # Fetch corporate action with lock to prevent concurrent processing
        ca = session.query(CorporateActionBase).filter_by(id=corporate_action_id) \
            .with_for_update().one_or_none()

        if not ca:
            raise CorporateActionError(f"Corporate action {corporate_action_id} not found")

        # Check processing status
        if ca.status == StatusEnum.CLOSED and not force_execution:
            logger.info("Corporate action already processed", extra={'status': ca.status})
            return {
                'status': 'already_processed',
                'corporate_action_id': corporate_action_id
            }

        # Validate execution timing
        if not force_execution and ca.execution_date > date.today():
            logger.info("Corporate action not due for execution",
                        extra={'execution_date': str(ca.execution_date)})
            return {
                'status': 'not_due',
                'corporate_action_id': corporate_action_id,
                'execution_date': str(ca.execution_date)
            }

        # Update task tracking
        ca.celery_task_id = self.request.id
        ca.status = StatusEnum.PROCESSING
        session.commit()

        # Create and validate executor
        executor = ca_execution_engine(ca)

        # Execute corporate action
        result = executor.execute()
        logger.info("Successfully processed corporate action",
                    extra={'result': result})

        return result

    except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.TimeoutError) as e:
        logger.critical("Database operation failed", exc_info=True)
        raise self.retry(countdown=120, max_retries=2, exc=e)

    except ProcessingLockError as e:
        logger.warning("Resource locked, retrying", exc_info=True)
        raise self.retry(countdown=60, max_retries=5, exc=e)

    except CorporateActionValidationError as e:
        logger.error("Validation failed", exc_info=True)
        if ca:
            ca.mark_failed(ca, {
                'error': str(e),
                'validation': True,
                'task_id': self.request.id
            })
            session.commit()
        return {
            'status': 'validation_failed',
            'error': str(e),
            'corporate_action_id': corporate_action_id
        }

    except Exception as e:
        logger.error("Unexpected processing error", exc_info=True)
        if ca:
            ca.mark_failed(ca, {
                'error': str(e),
                'task_id': self.request.id,
                'traceback': self.request.traceback
            })
            try:
                session.commit()
            except Exception:
                logger.error("Failed to record failure state", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Failed to process corporate action {corporate_action_id}: {str(e)}")
        # Mark as failed in database

        try:
            ca = session.get(CorporateActionBase, corporate_action_id)
            if ca:
                ca.mark_failed(ca, {
                    'error': str(e),
                    'task_id': self.request.id,
                    'traceback': self.request.traceback
                })
                session.commit()

        except Exception as db_error:
            logger.error(f"Failed to record failure in database: {str(db_error)}")
        raise


# def run_with_session(self, session: Session, *args, **kwargs):
#     return process_corporate_action(self, session, *args, **kwargs)


@celery_app.task(bind=True, base=DatabaseTask, name='corporate_actions.tasks.batch_process_eod_actions')
def batch_process_eod_actions(session: Session, target_date: Optional[str] = None,
                              chunk_size: int = 10, max_concurrency: int = 5) -> Dict[str, Any]:
    """Process all corporate actions due for execution with optimized batch processing"""

    execution_date = (datetime.strptime(target_date, '%Y-%m-%d').date()
                      if target_date else date.today())

    logger.info("Starting EOD batch processing", extra={
        'execution_date': str(execution_date),
        'chunk_size': chunk_size,
        'max_concurrency': max_concurrency
    })

    # Fetch pending actions with efficient query
    pending_actions = session.query(CorporateActionBase).filter(
        and_(
            CorporateActionBase.execution_date <= execution_date,
            CorporateActionBase.status == StatusEnum.PENDING
        )
    ).order_by(
        CorporateActionBase.priority.desc(),
        CorporateActionBase.execution_date,
        CorporateActionBase.created_at
    ).all()

    logger.info("Found pending corporate actions", extra={
        'count': len(pending_actions)
    })

    # Initialize results structure
    results = {
        'total_actions': len(pending_actions),
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'errors': [],
        'task_ids': [],
        'start_time': datetime.now().isoformat(),
        'execution_date': str(execution_date)
    }

    # Group and process by equity
    equity_actions = group_by_equity(pending_actions)

    # Process in parallel chunks with controlled concurrency
    for equity_id, actions in equity_actions.items():
        logger.info("Processing actions for equity", extra={
            'equity_id': equity_id,
            'action_count': len(actions)
        })

        # Process high priority actions first
        process_priority_actions(
            actions=[a for a in actions if a.priority == PriorityEnum.HIGH],
            results=results,
            synchronous=True
        )

        # Process normal priority in parallel
        process_priority_actions(
            actions=[a for a in actions if a.priority != PriorityEnum.HIGH],
            results=results,
            synchronous=False,
            chunk_size=chunk_size
        )

    # Finalize results
    results['end_time'] = datetime.now().isoformat()
    results['duration_seconds'] = (
            datetime.fromisoformat(results['end_time']) -
            datetime.fromisoformat(results['start_time'])
    ).total_seconds()

    logger.info("Completed EOD batch processing", extra={'results': results})
    return results


def group_by_equity(actions: List[CorporateActionBase]) -> Dict[int, List[CorporateActionBase]]:
    """Group actions by equity ID in chronological order"""
    equity_actions = {}
    for action in sorted(actions, key=lambda x: (x.execution_date, x.created_at)):
        if action.equity_id not in equity_actions:
            equity_actions[action.equity_id] = []
        equity_actions[action.equity_id].append(action)
    return equity_actions


def process_priority_actions(actions: List[CorporateActionBase],
                             results: Dict[str, Any], synchronous: bool,
                             chunk_size: int = 10) -> None:
    """Process a set of actions with specified priority handling"""
    if not actions:
        return

    if synchronous:
        # Process high priority actions one by one
        for action in actions:
            try:
                task_result = process_corporate_action.delay(action.id).get(timeout=300)
                if task_result.get('success'):
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'action_id': action.id,
                        'error': task_result.get('error', 'Unknown error')
                    })
            except Exception as e:
                logger.error("Failed to process high priority action", extra={
                    'action_id': action.id,
                    'error': str(e)
                })
                results['failed'] += 1
                results['errors'].append({
                    'action_id': action.id,
                    'error': str(e)
                })
    else:
        # Process normal priority in parallel chunks
        for chunk in chunked(actions, chunk_size):
            try:
                task_group = group(
                    process_corporate_action.s(action.id)
                    for action in chunk
                ).apply_async()
                results['task_ids'].extend(task.id for task in task_group.results)
                results['successful'] += len(chunk)  # Optimistic counting
            except Exception as e:
                logger.error("Failed to process action chunk", extra={
                    'chunk_size': len(chunk),
                    'error': str(e)
                })
                results['failed'] += len(chunk)
                results['errors'].append({
                    'chunk': [a.id for a in chunk],
                    'error': str(e)
                })


def chunked(iterable, size):
    """Yield successive chunks from an iterable"""
    it = iter(iterable)
    while chunk := list(islice(it, size)):
        yield chunk


# Monitoring and maintenance tasks
@celery_app.task(bind=True, base=DatabaseTask, name='corporate_actions.tasks.monitor_failed_actions')
def monitor_failed_actions(session: Session):
    """Monitor and report failed corporate actions"""
    try:
        from datetime import timedelta
        from sqlalchemy import func

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


@celery_app.task(bind=True, base=DatabaseTask, name='corporate_actions.tasks.cleanup_completed_tasks')
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


@celery_app.task(bind=True, base=DatabaseTask, name='corporate_actions.tasks.process_overdue_actions')
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
