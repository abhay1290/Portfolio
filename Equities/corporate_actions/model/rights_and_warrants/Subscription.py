from sqlalchemy import Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Subscription(CorporateActionBase):
    __tablename__ = 'subscription'
    API_Path = 'Subscription'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Subscription details
    subscription_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    subscription_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    minimum_subscription = Column(Integer, nullable=True)
    maximum_subscription = Column(Integer, nullable=True)

    # Dates
    offer_date = Column(Date, nullable=False)
    subscription_deadline = Column(Date, nullable=False)
    payment_deadline = Column(Date, nullable=False)
    allotment_date = Column(Date, nullable=True)

    # Subscription results
    shares_applied = Column(Integer, nullable=True)
    shares_allotted = Column(Integer, nullable=True)
    allotment_ratio = Column(Float, nullable=True)

    # Metadata
    subscription_purpose = Column(Text, nullable=True)
    subscription_notes = Column(Text, nullable=True)
