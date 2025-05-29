from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, func

from Currency.CurrencyEnum import CurrencyEnum
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.enums.PriorityEnum import PriorityEnum
from Equities.corporate_actions.enums.ProcessingModeEnum import ProcessingModeEnum
from Equities.corporate_actions.enums.StatusEnum import StatusEnum
from Equities.database import Base


class CorporateActionBase(Base):
    __tablename__ = 'corporate_action'
    API_Path = 'Corporate-Action'

    # Primary identifiers - absolutely mandatory for all corporate actions
    id = Column(Integer, primary_key=True, autoincrement=True)
    equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)

    # Timestamps - all records need these
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Core action details - minimal required to identify any corporate action
    action_type = Column(Enum(CorporateActionTypeEnum), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)

    # Status and processing - needed for workflow management
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    priority = Column(Enum(PriorityEnum), nullable=False, default=PriorityEnum.NORMAL)
    processing_mode = Column(Enum(ProcessingModeEnum), nullable=False, default=ProcessingModeEnum.AUTOMATIC)

    # Key dates - minimal set that applies to all corporate actions
    record_date = Column(Date, nullable=False)
    execution_date = Column(Date, nullable=False)

    # Flags - basic flags that apply to all actions
    is_mandatory = Column(Boolean, nullable=False, default=True)
    is_taxable = Column(Boolean, nullable=False, default=False)
