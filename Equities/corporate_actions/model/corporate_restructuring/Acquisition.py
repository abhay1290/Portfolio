from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Acquisition(CorporateActionBase):
    __tablename__ = 'acquisition'
    API_Path = 'Acquisition'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), primary_key=True)

    # Acquisition details
    acquiring_company_id = Column(Integer, ForeignKey('equity.id'), nullable=True)
    acquisition_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    acquisition_premium = Column(Float, nullable=True)

    # Dates
    announcement_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=False)

    # Transaction details
    acquisition_method = Column(String(100), nullable=True)  # "CASH", "STOCK", "MIXED"
    is_friendly = Column(Boolean, default=True, nullable=False)

    # Financial impact
    premium_over_market = Column(Float, nullable=True)

    # Metadata
    acquisition_notes = Column(Text, nullable=True)
