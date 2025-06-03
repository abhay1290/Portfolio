from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, Enum, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.enums.MergerTypeEnum import MergerTypeEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import MergerValidationError


class Merger(CorporateActionBase):
    __tablename__ = 'merger'
    API_Path = 'Merger'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Merger details
    acquiring_company_id = Column(Integer, ForeignKey('equity.id'), nullable=True)
    merger_type = Column(Enum(MergerTypeEnum), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Consideration details
    cash_consideration = Column(NUMERIC(precision=20, scale=6), nullable=True)
    stock_consideration_ratio = Column(NUMERIC(precision=10, scale=6), nullable=True)
    total_consideration_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_shares_handling = Column(String(50), nullable=False, default='ROUND')  # ROUND, PAY_CASH, FLOOR

    # Dates
    announcement_date = Column(Date, nullable=False)
    shareholder_approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)

    # Tax implications
    is_tax_free_reorganization = Column(Boolean, default=False, nullable=False)
    taxable_gain_recognition = Column(Boolean, default=True, nullable=False)

    # Financial impact
    implied_premium = Column(Float, nullable=True)
    synergy_estimate = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    merger_terms = Column(Text, nullable=True)
    merger_notes = Column(Text, nullable=True)

    def calculate_total_consideration(self, acquirer_price: float = None):
        """Calculate total consideration value"""
        if not self.equity or not self.equity.shares_outstanding:
            raise MergerValidationError("Missing equity information for calculation")

        total_value = Decimal(0)

        # Cash component
        if self.cash_consideration:
            total_value += Decimal(str(self.cash_consideration)) * self.equity.shares_outstanding

        # Stock component
        if self.stock_consideration_ratio and acquirer_price:
            total_value += Decimal(str(self.stock_consideration_ratio)) * Decimal(
                str(acquirer_price)) * self.equity.shares_outstanding

        self.total_consideration_value = total_value
        return total_value

    def calculate_implied_premium(self, target_market_cap: float):
        """Calculate implied premium over target's market cap"""
        if not self.total_consideration_value:
            raise MergerValidationError("Total consideration value not calculated")

        if target_market_cap <= 0:
            raise MergerValidationError("Target market cap must be positive")

        self.implied_premium = float(
            (self.total_consideration_value - Decimal(str(target_market_cap))) / Decimal(str(target_market_cap))
        )

    def mark_completed(self):
        """Mark the merger as completed"""
        self.is_completed = True

    def __repr__(self):
        return (f"<Merger(id={self.corporate_action_id}, "
                f"type={self.merger_type.value}, "
                f"completed={self.is_completed})>")
