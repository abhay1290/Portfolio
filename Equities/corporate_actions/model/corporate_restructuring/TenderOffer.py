from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class TenderOffer(CorporateActionBase):
    __tablename__ = 'tender_offer'
    API_Path = 'Tender-Offer'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Tender offer details
    offer_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    minimum_shares_sought = Column(Integer, nullable=True)
    maximum_shares_sought = Column(Integer, nullable=True)

    # Dates
    offer_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    withdrawal_deadline = Column(Date, nullable=True)
    proration_date = Column(Date, nullable=True)

    # Offer conditions
    is_conditional = Column(Boolean, default=False, nullable=False)
    minimum_tender_condition = Column(Float, nullable=True)  # Percentage

    # Results
    shares_tendered = Column(Integer, nullable=True)
    proration_factor = Column(Float, nullable=True)

    # Metadata
    offer_terms = Column(Text, nullable=True)
    tender_notes = Column(Text, nullable=True)
