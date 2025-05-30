from abc import ABC, abstractmethod

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.model.Equity import Equity
from Equities.utils.quantlib_mapper import to_ql_business_day_convention, to_ql_calendar, to_ql_day_count


class CorporateActionExecutorBase(ABC):
    def __int__(self, ca: CorporateActionBase):
        # self.equity_id = ca.equity_id
        self.equity = self._fetch_equity(ca.equity_id)

        # Equity level info ->
        # calculation setup
        self.calendar = to_ql_calendar(self.equity.calendar)
        self.day_count_convention = to_ql_day_count(self.equity.day_count_convention)
        self.business_day_convention = to_ql_business_day_convention(self.equity.business_day_convention)

        # Corporate Action info ->
        # Identifiers
        self.action_type = ca.action_type
        self.currency = ca.currency

        # Status and processing
        self.status = ca.status
        self.priority = ca.priority
        self.processing_mode = ca.processing_mode

        # Evaluation context
        self.record_date = ca.record_date
        self.execution_date = ca.execution_date

        # Flags
        self.is_mandatory = ca.is_mandatory
        self.is_taxable = ca.is_taxable

    @abstractmethod
    def execute(self):
        """Execute the corporate action"""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback corporate action if needed"""
        pass

    def _fetch_equity(equity_id: int) -> Equity:
        pass
