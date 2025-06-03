from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, NUMERIC, Text

from Equities.corporate_actions.enums.RightsStatusEnum import RightsStatusEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class RightsIssue(CorporateActionBase):
    __tablename__ = 'rights_issue'
    API_Path = 'Rights-Issue'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Rights details
    subscription_price = Column(NUMERIC(precision=20, scale=6), nullable=False)
    rights_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)
    subscription_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)

    # Dates
    announcement_date = Column(Date, nullable=True)
    ex_rights_date = Column(Date, nullable=False)
    rights_trading_start = Column(Date, nullable=True)
    rights_trading_end = Column(Date, nullable=True)
    subscription_deadline = Column(Date, nullable=False)

    # Rights valuation
    theoretical_rights_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    rights_trading_price = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Status tracking
    rights_status = Column(Enum(RightsStatusEnum), nullable=False, default=RightsStatusEnum.ACTIVE)

    # Metadata
    rights_purpose = Column(Text, nullable=True)
    rights_notes = Column(Text, nullable=True)

    def calculate_theoretical_rights_value(self, market_price):
        """Calculate theoretical rights value"""
        if market_price and self.subscription_price and self.rights_ratio:
            cum_rights_price = market_price
            ex_rights_price = (cum_rights_price + (self.subscription_price / self.rights_ratio)) / (
                    1 + (1 / self.rights_ratio))
            self.theoretical_rights_value = cum_rights_price - ex_rights_price

    def __repr__(self):
        return (
            f"<RightsIssue(id={self.corporate_action_id}, "
            f"subscription_price={self.subscription_price}, "
            f"ex_date='{self.ex_rights_date}')>"
        )
