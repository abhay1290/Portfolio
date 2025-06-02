from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text
from sqlalchemy.orm import validates

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import ReorganizationValidationError


class Reorganization(CorporateActionBase):
    __tablename__ = 'reorganization'
    API_Path = 'Reorganization'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Reorganization details
    reorganization_type = Column(String(100), nullable=False)  # e.g., "Merger", "Spin-off", "Split-off"
    new_entity_id = Column(Integer, ForeignKey('equity.id'), nullable=True)

    # Exchange terms
    exchange_ratio = Column(NUMERIC(precision=10, scale=6), nullable=True)
    cash_component = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_shares_handling = Column(String(50), nullable=True)  # "Cash", "Round-up", "Round-down"

    # Dates
    announcement_date = Column(Date, nullable=False)
    record_date = Column(Date, nullable=True)
    shareholder_meeting_date = Column(Date, nullable=True)
    shareholder_approval_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)
    completion_date = Column(Date, nullable=True)

    # Tax and regulatory
    is_tax_free = Column(Boolean, default=False, nullable=False)
    regulatory_approval_required = Column(Boolean, default=True, nullable=False)

    # Status tracking
    # reorganization_status = Column(Enum(ReorganizationStatusEnum), nullable=False, default=ReorganizationStatusEnum.PENDING)

    # Valuation
    implied_premium = Column(NUMERIC(precision=10, scale=6), nullable=True)  # Premium/discount to market price
    pro_forma_impact = Column(NUMERIC(precision=10, scale=6), nullable=True)  # EPS impact, etc.

    # Metadata
    reorganization_purpose = Column(Text, nullable=True)
    reorganization_notes = Column(Text, nullable=True)

    @validates('exchange_ratio')
    def validate_exchange_ratio(self, value):
        if value is not None and value <= 0:
            raise ReorganizationValidationError("Exchange ratio must be positive if specified")
        return value

    @validates('cash_component')
    def validate_cash_component(self, value):
        if value is not None and value < 0:
            raise ReorganizationValidationError("Cash component cannot be negative")
        return value

    @validates('announcement_date', 'effective_date')
    def validate_dates(self, key, date_value):
        if date_value is None:
            raise ReorganizationValidationError(f"{key} cannot be None")
        return date_value

    def calculate_implied_premium(self, market_price, new_entity_price):
        """Calculate implied premium/discount based on exchange terms"""
        if (market_price and new_entity_price and
                self.exchange_ratio is not None and
                self.cash_component is not None):
            implied_value = (new_entity_price * self.exchange_ratio) + self.cash_component
            self.implied_premium = (implied_value - market_price) / market_price

    def __repr__(self):
        return (
            f"<Reorganization(id={self.corporate_action_id}, "
            f"type='{self.reorganization_type}', "
            f"effective='{self.effective_date}')>"
        )
