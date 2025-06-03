from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase


class Delisting(CorporateActionBase):
    __tablename__ = 'delisting'
    API_Path = 'Delisting'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Delisting details
    delisting_reason = Column(String(255), nullable=False)  # "Merger", "Bankruptcy", "Regulatory", "Voluntary"
    is_voluntary = Column(Boolean, default=False, nullable=False)
    final_trading_date = Column(Date, nullable=False)
    delisting_code = Column(String(50), nullable=True)  # Exchange-specific code

    # New trading venue (if applicable)
    new_exchange = Column(String(100), nullable=True)
    new_symbol = Column(String(20), nullable=True)
    new_security_type = Column(String(50), nullable=True)  # "Private", "OTC", "Other Exchange"

    # Dates
    announcement_date = Column(Date, nullable=False)
    notification_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=False)
    appeal_deadline = Column(Date, nullable=True)

    # Status tracking
    # delisting_status = Column(Enum(DelistingStatusEnum), nullable=False, default=DelistingStatusEnum.ANNOUNCED)

    # Impact on shareholders
    shareholder_impact = Column(Text, nullable=True)
    alternative_trading_info = Column(Text, nullable=True)
    delisting_notes = Column(Text, nullable=True)

    # Valuation impact
    last_trading_price = Column(NUMERIC(precision=20, scale=6), nullable=True)
    implied_liquidation_value = Column(NUMERIC(precision=20, scale=6), nullable=True)

    def record_last_trading_price(self, key, price):
        """Record the last trading price before delisting"""
        if price and price > 0:
            self.last_trading_price = price

    def __repr__(self):
        return (
            f"<Delisting(id={self.corporate_action_id}, "
            f"reason='{self.delisting_reason}', "
            f"effective='{self.effective_date}')>"
        )
