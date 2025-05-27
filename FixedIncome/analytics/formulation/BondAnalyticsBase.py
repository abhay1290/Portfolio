from abc import ABC, abstractmethod
from datetime import date

from FixedIncome.analytics.utils.quantlib_mapper import to_ql_business_day_convention, to_ql_calendar, \
    to_ql_compounding, to_ql_date, to_ql_day_count, \
    to_ql_frequency
from FixedIncome.model.BondBase import BondBase


class BondAnalyticsBase(ABC):
    def __init__(self, bond: BondBase):
        # Basic bond metadata
        self.symbol = bond.symbol
        self.bond_type = bond.bond_type
        self.currency = bond.currency

        # Lifecycle dates
        self.issue_date = to_ql_date(bond.issue_date)
        self.maturity_date = to_ql_date(bond.maturity_date)

        # Evaluation context
        self.evaluation_date = to_ql_date(bond.evaluation_date)
        self.settlement_days = bond.settlement_days
        self.calendar = to_ql_calendar(bond.calendar)

        # Financial values
        self.face_value = bond.face_value
        self.market_price = bond.market_price

        # Interest rate conventions
        self.day_count_convention = to_ql_day_count(bond.day_count_convention)
        self.compounding = to_ql_compounding(bond.compounding)
        self.frequency = to_ql_frequency(bond.frequency)
        self.business_day_convention = to_ql_business_day_convention(bond.business_day_convention)

    @abstractmethod
    def _get_normalized_market_price(self):
        pass

    @abstractmethod
    def build_quantlib_bond(self):
        pass

    @abstractmethod
    def cashflows(self) -> list:
        pass

    @abstractmethod
    def clean_price(self) -> float:
        pass

    @abstractmethod
    def dirty_price(self) -> float:
        pass

    @abstractmethod
    def accrued_interest(self) -> float:
        pass

    @abstractmethod
    def yield_to_maturity(self) -> float:
        pass

    @abstractmethod
    def yield_to_worst(self) -> float:
        pass

    @abstractmethod
    def modified_duration(self) -> float:
        pass

    @abstractmethod
    def macaulay_duration(self) -> float:
        pass

    @abstractmethod
    def simple_duration(self) -> float:
        pass

    @abstractmethod
    def convexity(self) -> float:
        pass

    @abstractmethod
    def dv01(self) -> float:
        pass

    @abstractmethod
    def summary(self) -> dict:
        pass

    @abstractmethod
    def get_discount_curve(self):
        pass

    @abstractmethod
    def update_yield_curve(self, rate: float):
        pass

    @abstractmethod
    def update_evaluation_date(self, new_date: date):
        pass
