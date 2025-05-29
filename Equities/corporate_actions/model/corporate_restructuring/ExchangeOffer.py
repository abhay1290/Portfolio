from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class ExchangeOffer(CorporateActionBase):
    __tablename__ = 'exchange_offer'
    API_Path = 'Exchange-Offer'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Exchange details
    new_security_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    exchange_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    cash_component = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Dates
    offer_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    settlement_date = Column(Date, nullable=True)

    # Conditions
    minimum_participation = Column(Float, nullable=True)
    is_mandatory = Column(Boolean, default=False, nullable=False)

    # Metadata
    exchange_terms = Column(Text, nullable=True)
    exchange_notes = Column(Text, nullable=True)
