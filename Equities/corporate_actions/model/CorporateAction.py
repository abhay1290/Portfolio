from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, func

from Currency.CurrencyEnum import CurrencyEnum
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.StatusEnum import StatusEnum
from Equities.database import Base


class CorporateAction(Base):
    __tablename__ = 'corporate_action'
    API_Path = 'Corporate-Action'

    id = Column(Integer, primary_key=True, autoincrement=True)
    equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company_name = Column(String, nullable=True)
    action_type = Column(Enum(CorporateActionTypeEnum), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)  # may differ from equity
    status = Column(Enum(StatusEnum), nullable=False)

    record_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=False)

    details = Column(String, nullable=True)
