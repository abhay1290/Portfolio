from sqlalchemy import Column, Date, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Subscription(CorporateActionBase):
    __tablename__ = 'subscription'
    API_Path = 'Subscription'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Subscription details
    subscription_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    subscription_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    minimum_subscription = Column(Integer, nullable=True)
    maximum_subscription = Column(Integer, nullable=True)

    # Dates
    announcement_date = Column(Date, nullable=True)
    offer_date = Column(Date, nullable=False)
    subscription_deadline = Column(Date, nullable=False)
    payment_deadline = Column(Date, nullable=False)
    allotment_date = Column(Date, nullable=True)

    # Subscription results
    shares_applied = Column(Integer, nullable=True)
    shares_allotted = Column(Integer, nullable=True)
    allotment_ratio = Column(NUMERIC(precision=10, scale=6), nullable=True)
    subscription_premium = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Status tracking
    # subscription_status = Column(Enum(SubscriptionStatusEnum), nullable=False, default=SubscriptionStatusEnum.OPEN)

    # Metadata
    subscription_purpose = Column(Text, nullable=True)
    subscription_notes = Column(Text, nullable=True)

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
