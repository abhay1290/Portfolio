from datetime import date

from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Subscription(CorporateActionBase):
    __tablename__ = 'subscription'
    API_Path = 'Subscription'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Required fields
    subscription_price = Column(Numeric(precision=20, scale=6), nullable=False)
    subscription_ratio = Column(Numeric(precision=10, scale=6), nullable=False)
    offer_date = Column(Date, nullable=False)
    subscription_deadline = Column(Date, nullable=False)
    payment_deadline = Column(Date, nullable=False)

    # Fields with defaults
    minimum_subscription = Column(Integer, nullable=False, default=1)
    maximum_subscription = Column(Integer, nullable=False, default=1000000)
    announcement_date = Column(Date, nullable=False, default=date.today)
    allotment_date = Column(Date, nullable=False, default=date.today)

    # Result fields
    shares_applied = Column(Integer, nullable=False, default=0)
    shares_allotted = Column(Integer, nullable=False, default=0)
    allotment_ratio = Column(Numeric(precision=10, scale=6), nullable=False, default=0.0)
    subscription_premium = Column(Numeric(precision=20, scale=6), nullable=False, default=0.0)

    # Additional info
    subscription_purpose = Column(Text, nullable=False, default='')
    subscription_notes = Column(Text, nullable=False, default='')

    # @validates('subscription_price')
    # def validate_subscription_price(self, key, value):
    #     if value is None or value <= 0:
    #         raise SubscriptionValidationError("Subscription price must be positive")
    #     return value
    #
    # @validates('subscription_ratio')
    # def validate_subscription_ratio(self, key, value):
    #     if value is None or value <= 0:
    #         raise SubscriptionValidationError("Subscription ratio must be positive")
    #     return value
    #
    # @validates('minimum_subscription', 'maximum_subscription')
    # def validate_subscription_limits(self, key, value):
    #     if value is not None and value <= 0:
    #         raise SubscriptionValidationError(f"{key} must be positive if specified")
    #     return value
    #
    # @validates('offer_date', 'subscription_deadline', 'payment_deadline')
    # def validate_dates(self, key, date_value):
    #     if date_value is None:
    #         raise SubscriptionValidationError(f"{key} cannot be None")
    #     return date_value

    def calculate_subscription_premium(self, market_price):
        """Calculate premium over market price"""
        if market_price and self.subscription_price:
            self.subscription_premium = (self.subscription_price - market_price) / market_price

    def __repr__(self):
        return (
            f"<Subscription(id={self.corporate_action_id}, "
            f"price={self.subscription_price}, "
            f"deadline='{self.subscription_deadline}')>"
        )
