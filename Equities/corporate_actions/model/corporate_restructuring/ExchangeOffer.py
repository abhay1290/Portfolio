from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import ExchangeOfferValidationError


class ExchangeOffer(CorporateActionBase):
    __tablename__ = 'exchange_offer'
    API_Path = 'Exchange-Offer'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Exchange details
    new_security_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    exchange_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    cash_component = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_shares_handling = Column(String(50), nullable=False, default='ROUND')  # ROUND, PAY_CASH, FLOOR

    # Dates
    offer_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)

    # Conditions
    minimum_participation = Column(Float, nullable=True)
    is_voluntary = Column(Boolean, default=True, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Metadata
    exchange_terms = Column(Text, nullable=True)
    exchange_notes = Column(Text, nullable=True)

    # Calculated fields
    implied_premium = Column(Float, nullable=True)
    participation_rate = Column(Float, nullable=True)

    # @validates('exchange_ratio')
    # def validate_exchange_ratio(self, key, ratio):
    #     if ratio is None or ratio <= 0:
    #         raise ExchangeOfferValidationError("Exchange ratio must be positive")
    #     return ratio
    #
    # @validates('cash_component')
    # def validate_cash_component(self, key, cash):
    #     if cash is not None and cash < 0:
    #         raise ExchangeOfferValidationError("Cash component cannot be negative")
    #     return cash
    #
    # @validates('minimum_participation')
    # def validate_minimum_participation(self, key, participation):
    #     if participation is not None and (participation <= 0 or participation > 1):
    #         raise ExchangeOfferValidationError("Minimum participation must be between 0 and 1")
    #     return participation
    #
    # @validates('offer_date', 'expiration_date')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise ExchangeOfferValidationError(f"{key} cannot be None")
    #     return date_value

    def calculate_implied_premium(self, new_security_price: float):
        """Calculate the implied premium based on new security price"""
        if not self.equity or not self.equity.market_price:
            raise ExchangeOfferValidationError("Original security price not available")

        implied_value = (self.exchange_ratio * new_security_price) + (self.cash_component or 0)
        self.implied_premium = (implied_value - self.equity.market_price) / self.equity.market_price

    def mark_completed(self, actual_settlement_date, actual_participation_rate: float = None):
        """Mark the exchange offer as completed"""
        self.settlement_date = actual_settlement_date
        self.participation_rate = actual_participation_rate
        self.is_completed = True

    def __repr__(self):
        return (f"<ExchangeOffer(id={self.corporate_action_id}, "
                f"ratio={self.exchange_ratio}, "
                f"cash={self.cash_component}, "
                f"completed={self.is_completed})>")
