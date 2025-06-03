import logging
from datetime import date, datetime
from itertools import islice
from typing import Any, Dict, List, Optional

import sqlalchemy
from celery import Task, group
from sqlalchemy import and_
from sqlalchemy.orm import Session, with_polymorphic

from celery_app import celery_app
from equity.src.database.database import SessionLocal
from equity.src.model import CorporateActionHistoryLog
from equity.src.model import Equity
from equity.src.model.corporate_actions.analytics.CorporateActionExecutionEngine import ca_execution_engine
from equity.src.model.corporate_actions.enums.PriorityEnum import PriorityEnum
from equity.src.model.corporate_actions.enums.StatusEnum import StatusEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase
from equity.src.model.corporate_actions.model.cash_distribution.Distribution import Distribution
from equity.src.model.corporate_actions.model.cash_distribution.Dividend import Dividend
from equity.src.model.corporate_actions.model.cash_distribution.ReturnOfCapital import ReturnOfCapital
from equity.src.model.corporate_actions.model.cash_distribution.SpecialDividend import SpecialDividend
from equity.src.model.corporate_actions.model.corporate_restructuring.Acquisition import Acquisition
from equity.src.model.corporate_actions.model.corporate_restructuring.ExchangeOffer import ExchangeOffer
from equity.src.model.corporate_actions.model.corporate_restructuring.Merger import Merger
from equity.src.model.corporate_actions.model.corporate_restructuring.TenderOffer import TenderOffer
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Bankruptcy import Bankruptcy
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Delisting import Delisting
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Liquidation import Liquidation
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Reorganization import Reorganization
from equity.src.model.corporate_actions.model.rights_and_warrants.RightsIssue import RightsIssue
from equity.src.model.corporate_actions.model.rights_and_warrants.Subscription import Subscription
from equity.src.model.corporate_actions.model.rights_and_warrants.WarrentExercise import WarrantExercise
from equity.src.model.corporate_actions.model.stock_changes.ReverseSplit import ReverseSplit
from equity.src.model.corporate_actions.model.stock_changes.SpinOff import SpinOff
from equity.src.model.corporate_actions.model.stock_changes.StockDividend import StockDividend
from equity.src.model.corporate_actions.model.stock_changes.StockSplit import StockSplit
from equity.src.utils.Exceptions import CorporateActionError, CorporateActionValidationError, ProcessingLockError

logger = logging.getLogger(__name__)


class CorporateActionTask(Task):
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
        if CorporateActionTask._session_pool is None:
            CorporateActionTask.initialize_pool()
        self._session = None

    def get_session(self):
        """Get a session from the pool"""
        if self._session is None:
            self._session = CorporateActionTask._session_pool.pop()
        return self._session

    def release_session(self):
        """Release the session back to the pool"""
        if self._session is not None:
            CorporateActionTask._session_pool.append(self._session)
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


@celery_app.task(bind=True, base=CorporateActionTask, name='corporate_actions.process_single')
def process_single_corporate_action(self, session: Session, corporate_action_id: int,
                                    force_execution: bool = False) -> Dict[str, Any]:
    """Process a single corporate action with enhanced error handling and validation"""

    logger.info(f"Processing corporate action {corporate_action_id}", extra={
        'corporate_action_id': corporate_action_id,
        'force_execution': force_execution
    })
    ca = None
    try:
        # Declare all possible subclasses
        CorporateAction = with_polymorphic(
            CorporateActionBase,
            [Dividend, Distribution, ReturnOfCapital, SpecialDividend, Acquisition, ExchangeOffer, Merger, TenderOffer,
             Bankruptcy, Delisting, Liquidation, Reorganization, RightsIssue, Subscription, WarrantExercise,
             ReverseSplit,
             SpinOff, StockDividend, StockSplit]  # Add all subclasses here
        )
        # Fetch corporate action with lock to prevent concurrent processing
        ca: CorporateAction = session.query(CorporateActionBase).filter_by(id=corporate_action_id) \
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
        return {
            'status': 'success',
            'ca_id': corporate_action_id,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

    except (sqlalchemy.exc.OperationalError, sqlalchemy.exc.TimeoutError) as e:
        logger.critical("Database operation failed", exc_info=True)
        raise self.retry(countdown=120, max_retries=2, exc=e)

    except ProcessingLockError as e:
        logger.warning("Resource locked, retrying", exc_info=True)
        raise self.retry(countdown=60, max_retries=5, exc=e)

    except CorporateActionValidationError as e:
        logger.error(f"Validation failed for CA {corporate_action_id}: {str(e)}")
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
        logger.error(f"Failed to process CA {corporate_action_id}: {str(e)}", exc_info=True)
        if ca:
            ca.mark_failed(ca, {
                'error': str(e),
                'task_id': self.request.id,
                'traceback': self.request.traceback
            })
            session.commit()

        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        session.close()


@celery_app.task(bind=True, base=CorporateActionTask, name='corporate_actions.tasks.batch_process_eod_actions')
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
    # Declare all possible subclasses
    CorporateAction = with_polymorphic(
        CorporateActionBase,
        [Dividend, Distribution, ReturnOfCapital, SpecialDividend, Acquisition, ExchangeOffer, Merger, TenderOffer,
         Bankruptcy, Delisting, Liquidation, Reorganization, RightsIssue, Subscription, WarrantExercise, ReverseSplit,
         SpinOff, StockDividend, StockSplit]  # Add all subclasses here
    )
    # Fetch pending actions with efficient query
    pending_actions: List[CorporateAction] = session.query(CorporateActionBase).filter(
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


@celery_app.task(bind=True, base=CorporateActionTask, name='corporate_actions.rollback')
def rollback_corporate_action(self, ca_id: int, rollback_reason: str) -> Dict[str, Any]:
    """Rollback a corporate action and reprocess subsequent actions"""
    session = self.get_session()
    try:
        # Get the corporate action to rollback
        ca = session.query(CorporateActionBase).filter_by(id=ca_id).one_or_none()
        if not ca:
            raise CorporateActionError(f"Corporate action {ca_id} not found")

        # Get the equity
        equity = session.query(Equity).filter_by(id=ca.equity_id).one()

        # Find the log entry for this action
        log_entry = session.query(CorporateActionHistoryLog).filter_by(
            equity_id=equity.id,
            action_id=str(ca_id)
        ).order_by(CorporateActionHistoryLog.executed_at.desc()).first()

        if not log_entry:
            raise CorporateActionError(f"No log entry found for corporate action {ca_id}")

        # Rollback to the state before this action
        equity.rollback_to_state(
            session=session,
            log_id=log_entry.id,
            rollback_reason=rollback_reason
        )

        # Reset the corporate action status
        ca.status = StatusEnum.PENDING
        ca.last_error = None
        session.commit()

        # Get all subsequent actions that need reprocessing
        subsequent_actions = session.query(CorporateActionBase).filter(
            and_(
                CorporateActionBase.equity_id == equity.id,
                CorporateActionBase.execution_date >= ca.execution_date,
                CorporateActionBase.status == StatusEnum.CLOSED
            )
        ).order_by(CorporateActionBase.execution_date).all()

        # Reprocess subsequent actions
        reprocess_results = []
        for subsequent_ca in subsequent_actions:
            subsequent_ca.status = StatusEnum.PENDING
            session.commit()

            result = process_single_corporate_action.delay(subsequent_ca.id)
            reprocess_results.append(result.get())

        return {
            'status': 'completed',
            'original_ca_id': ca_id,
            'rollback_log_id': log_entry.id,
            'reprocessed_count': len(subsequent_actions),
            'reprocess_results': reprocess_results,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Rollback failed for CA {ca_id}: {str(e)}", exc_info=True)
        raise self.retry(exc=e, countdown=120, max_retries=3)

    finally:
        session.close()


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
                task_result = process_single_corporate_action.delay(action.id).get(timeout=300)
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
                    process_single_corporate_action.s(action.id)
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
