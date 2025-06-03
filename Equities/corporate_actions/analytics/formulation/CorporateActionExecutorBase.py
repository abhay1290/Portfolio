import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, Optional, Type

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.database import SessionLocal
from Equities.model.Equity import Equity
from Equities.utils.Decorators import audit_trail, performance_monitor, retry_on_failure, transaction_rollback
from Equities.utils.Exceptions import CorporateActionError
from Equities.utils.quantlib_mapper import from_ql_date, to_ql_business_day_convention, to_ql_calendar, to_ql_date


class CorporateActionExecutorBase(ABC):
    def __init__(self, ca: CorporateActionBase, session: Optional[Session] = None):
        self.corporate_action = ca
        self.session = session or SessionLocal()
        self.equity = self._fetch_equity(ca.equity_id)
        self.execution_context = {}
        self.validation_errors = []

        # Set up calculation context
        self._setup_calculation_context()

        # Initialize executor-specific attributes
        self._initialize_executor()

    def _setup_calculation_context(self):
        """Setup calculation context from equity and corporate action"""
        self.calendar = to_ql_calendar(self.equity.calendar)
        self.business_day_convention = to_ql_business_day_convention(self.equity.business_day_convention)
        self.equity_market_price = self.equity.market_price

        # Corporate Action context
        self.action_type = self.corporate_action.action_type
        self.currency = self.corporate_action.currency
        self.status = self.corporate_action.status
        self.priority = self.corporate_action.priority
        self.processing_mode = self.corporate_action.processing_mode
        self.record_date = self.corporate_action.record_date
        self.execution_date = self.corporate_action.execution_date
        self.is_mandatory = self.corporate_action.is_mandatory
        self.is_taxable = self.corporate_action.is_taxable

    @abstractmethod
    def _initialize_executor(self):
        """Initialize executor-specific attributes"""
        pass

    @abstractmethod
    def validate_prerequisites(self) -> bool:
        """Validate prerequisites for execution"""
        pass

    @abstractmethod
    def calculate_impacts(self) -> Dict[str, Any]:
        """Calculate the financial impacts of the corporate action"""
        pass

    @abstractmethod
    def execute_action(self) -> Dict[str, Any]:
        """Execute the corporate action"""
        pass

    @abstractmethod
    def post_execution_validation(self) -> bool:
        """Validate the execution results"""
        pass

    @performance_monitor
    @transaction_rollback
    @audit_trail
    def execute(self) -> Dict[str, Any]:
        """Main execution method with comprehensive error handling"""
        execution_result = {
            'success': False,
            'corporate_action_id': self.corporate_action.id,
            'equity_id': self.equity.id,
            'start_time': datetime.now(),
            'errors': [],
            'warnings': [],
            'execution_data': {}
        }

        try:
            # Mark as processing
            self.corporate_action.mark_processing()

            with self.equity.lock_for_processing(self.session):
                # 1. Validate prerequisites
                if not self.validate_prerequisites():
                    raise CorporateActionError(f"Prerequisites validation failed: {self.validation_errors}")

                # 2. Calculate impacts
                impact_data = self.calculate_impacts()
                execution_result['execution_data']['impacts'] = impact_data

                # 3. Execute the action
                action_result = self.execute_action()
                execution_result['execution_data']['action_result'] = action_result

                # 4. Post-execution validation
                if not self.post_execution_validation():
                    raise CorporateActionError("Post-execution validation failed")

                # 5. Log the corporate action
                log_id = self._log_corporate_action(impact_data, action_result)
                execution_result['execution_data']['log_id'] = log_id

                # 6. Mark as completed
                self.corporate_action.mark_completed()

                execution_result['success'] = True
                execution_result['end_time'] = datetime.now()

                logging.info(f"Successfully executed corporate action {self.corporate_action.id}")

        except Exception as e:
            # Mark as failed
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }

            self.corporate_action.mark_failed(error_details)
            execution_result['errors'].append(error_details)
            execution_result['end_time'] = datetime.now()

            logging.error(f"Failed to execute corporate action {self.corporate_action.id}: {str(e)}")
            raise

        return execution_result

    @retry_on_failure(max_retries=2, delay=0.5, exceptions=(SQLAlchemyError,))
    def _fetch_equity(self, equity_id: int) -> Type[Equity]:
        """Fetch equity with retry logic"""
        equity = self.session.get(Equity, equity_id)
        if not equity:
            raise CorporateActionError(f"Equity not found for ID: {equity_id}")
        return equity

    def _adjust_date(self, date_input: datetime) -> Optional[date]:
        """Adjust date according to business day convention and calendar"""
        if date_input is None:
            return None

        ql_date = to_ql_date(date_input)
        adjusted_date = self.calendar.adjust(ql_date, self.business_day_convention)
        return from_ql_date(adjusted_date)

    def _is_business_day(self, date_input: datetime) -> bool:
        """Check if date is a business day"""
        if date_input is None:
            return False

        ql_date = to_ql_date(date_input)
        return self.calendar.isBusinessDay(ql_date)

    def _log_corporate_action(self, impact_data: Dict[str, Any],
                              action_result: Dict[str, Any]) -> int:
        """Log corporate action execution"""
        action_parameters = {
            **impact_data,
            **action_result,
            'execution_context': self.execution_context
        }

        return self.equity.log_corporate_action(
            session=self.session,
            action_type=self.action_type,
            action_parameters=action_parameters,
            effective_date=datetime.combine(self.execution_date, datetime.min.time()),
            action_id=self.corporate_action.external_id,
            description=f"{self.action_type.value} execution",
            created_by="system",
            external_source=self.corporate_action.source_system,
            confidence_score=1.0
        )

    # def rollback(self, log_id: int, reason: str) -> bool:
    #     """Rollback corporate action execution"""
    #     try:
    #         with self.equity.lock_for_processing(self.session):
    #             self.equity.rollback_to_state(
    #                 session=self.session,
    #                 log_id=log_id,
    #                 rollback_reason=reason,
    #                 rolled_back_by="system"
    #             )
    #
    #             # Reset corporate action status
    #             self.corporate_action.reset_for_retry()
    #
    #         logging.info(f"Successfully rolled back corporate action {self.corporate_action.id}")
    #         return True
    #
    #     except Exception as e:
    #         logging.error(f"Failed to rollback corporate action {self.corporate_action.id}: {str(e)}")
    #         return False
