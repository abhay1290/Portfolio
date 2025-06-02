from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.utils.Exceptions import TenderOfferValidationError


class TenderOffer(CorporateActionBase):
    __tablename__ = 'tender_offer'
    API_Path = 'Tender-Offer'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Tender offer details
    offer_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    minimum_shares_sought = Column(Integer, nullable=True)
    maximum_shares_sought = Column(Integer, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Dates
    offer_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    withdrawal_deadline = Column(Date, nullable=True)
    proration_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)

    # Offer conditions
    offer_type = Column(String(50), nullable=False, default='CASH')  # CASH, STOCK, MIXED
    is_conditional = Column(Boolean, default=False, nullable=False)
    minimum_tender_condition = Column(Float, nullable=True)  # Percentage
    is_going_private = Column(Boolean, default=False, nullable=False)

    # Results
    shares_tendered = Column(Integer, nullable=True)
    shares_accepted = Column(Integer, nullable=True)
    proration_factor = Column(Float, nullable=True)
    final_price = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Financial impact
    premium_over_market = Column(Float, nullable=True)
    total_consideration = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Metadata
    offer_terms = Column(Text, nullable=True)
    tender_notes = Column(Text, nullable=True)

    # @validates('offer_price')
    # def validate_offer_price(self, key, price):
    #     if price is None or price <= 0:
    #         raise TenderOfferValidationError("Offer price must be positive")
    #     return price
    #
    # @validates('minimum_tender_condition')
    # def validate_minimum_tender(self, key, condition):
    #     if condition is not None and (condition <= 0 or condition > 1):
    #         raise TenderOfferValidationError("Minimum tender condition must be between 0 and 1")
    #     return condition
    #
    # @validates('offer_date', 'expiration_date')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise TenderOfferValidationError(f"{key} cannot be None")
    #     return date_value

    def calculate_premium(self, key, market_price: float):
        """Calculate premium over market price"""
        if market_price <= 0:
            raise TenderOfferValidationError("Market price must be positive")
        self.premium_over_market = (float(self.offer_price) - market_price) / market_price

    def calculate_total_consideration(self):
        """Calculate total consideration based on shares accepted"""
        if self.shares_accepted is None:
            raise TenderOfferValidationError("Shares accepted not set")
        self.total_consideration = self.offer_price * self.shares_accepted

    def mark_completed(self, actual_completion_date, shares_tendered: int, shares_accepted: int):
        """Mark the tender offer as completed"""
        self.completion_date = actual_completion_date
        self.shares_tendered = shares_tendered
        self.shares_accepted = shares_accepted
        self.is_completed = True

        # Calculate proration factor if applicable
        if (self.maximum_shares_sought and
                shares_tendered > self.maximum_shares_sought):
            self.proration_factor = self.maximum_shares_sought / shares_tendered

    def __repr__(self):
        return (f"<TenderOffer(id={self.corporate_action_id}, "
                f"price={self.offer_price}, "
                f"completed={self.is_completed})>")
