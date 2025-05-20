from abc import ABC, abstractmethod

from QuantLib import *

from FixedIncome.analytics.utils.quantlib_helpers import to_ql_date, to_ql_day_count
from FixedIncome.model.BondBase import BondBase


class BondAnalyticsBase(ABC):
    def __init__(self, bond: BondBase):
        self.bond_type = bond.bond_type
        self.day_count_convention = to_ql_day_count(bond.day_count_convention)

        self.face_value = bond.face_value
        self.market_price = bond.market_price

        self.issue_date = to_ql_date(bond.issue_date)
        self.maturity_date = to_ql_date(bond.maturity_date)
        self.settlement_date = bond.settlement_date
        self.settlement_days = bond.settlement_days

        self.credit_rating = bond.credit_rating

        self.calendar = TARGET()
        self.convention = Following

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
