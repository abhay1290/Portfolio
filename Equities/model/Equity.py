import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import Boolean, Column, DateTime, Enum, Index, Integer, NUMERIC, String, exists, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session, relationship, validates

from Currency.CurrencyEnum import CurrencyEnum
from Equities.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.database import Base
from Equities.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from Equities.enums.CalenderEnum import CalendarEnum
from Equities.model.CorporateActionHistoryLog import CorporateActionHistoryLog
from Equities.utils.Decorators import audit_trail, transaction_rollback, validation_required
from Equities.utils.Exceptions import CorporateActionError, EquityValidationError


class Equity(Base):
    __tablename__ = 'equity'
    __table_args__ = (
        Index('idx_equity_symbol', 'symbol'),
        Index('idx_equity_currency', 'currency'),
        Index('idx_equity_updated_at', 'updated_at'),
    )
    API_Path = "Equity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    version = Column(Integer, default=1, nullable=False)  # For optimistic locking

    # Identifiers
    symbol = Column(String(10000), nullable=False)
    # symbol = Column(String(20), nullable=False, unique=True)

    # Financial values with higher precision
    currency = Column(Enum(CurrencyEnum), nullable=False)
    market_price = Column(NUMERIC(precision=20, scale=6), nullable=True)
    shares_outstanding = Column(NUMERIC(precision=20, scale=0), nullable=True)
    float_shares = Column(NUMERIC(precision=20, scale=0), nullable=True)
    market_cap = Column(NUMERIC(precision=20, scale=2), nullable=True)

    # Evaluation context
    calendar = Column(Enum(CalendarEnum), nullable=False, default=CalendarEnum.TARGET)
    business_day_convention = Column(Enum(BusinessDayConventionEnum), nullable=False,
                                     default=BusinessDayConventionEnum.FOLLOWING)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)  # For processing locks
    last_processed_at = Column(DateTime(timezone=True), nullable=True)

    # corporate_action_ids = Column(JSONB, nullable=True, default=list)

    # Relationships
    corporate_action_history_log = relationship(
        "CorporateActionHistoryLog",
        back_populates="equity",
        cascade="all, delete-orphan",
        order_by="CorporateActionHistoryLog.executed_at"
    )

    corporate_actions = relationship(
        "CorporateActionBase",
        back_populates="equity",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Equity(id={self.id}, symbol='{self.symbol}', currency='{self.currency}')>"

    # @validates('symbol')
    # def validate_symbol(self, key, symbol):
    #     if not symbol or len(symbol.strip()) == 0:
    #         raise EquityValidationError("Symbol cannot be empty")
    #     return symbol.upper().strip()

    @validates('market_price', 'shares_outstanding', 'float_shares')
    def validate_positive_numbers(self, key, value):
        if value is not None and value < 0:
            raise EquityValidationError(f"{key} cannot be negative")
        return value

    @hybrid_property
    def calculated_market_cap(self):
        """Calculate market cap from price and shares outstanding"""
        if self.market_price and self.shares_outstanding:
            return self.market_price * self.shares_outstanding
        return None

    # # Event listeners for automatic market cap calculation
    # @event.listens_for(Equity.market_price, 'set')
    # @event.listens_for(Equity.shares_outstanding, 'set')
    # def calculate_market_cap(target, value, oldvalue, initiator):
    #     """Automatically calculate market cap when price or shares change"""
    #     if target.market_price and target.shares_outstanding:
    #         target.market_cap = target.market_price * target.shares_outstanding

    @contextmanager
    def lock_for_processing(self, session: Session):
        """Context manager for processing locks"""
        if self.is_locked:
            raise CorporateActionError(f"Equity {self.symbol} is already locked for processing")

        try:
            self.is_locked = True
            session.commit()
            yield self
        finally:
            self.is_locked = False
            session.commit()

    @audit_trail
    def capture_current_state(self) -> Dict[str, Any]:
        """Capture current state of equity for history logging."""
        return {
            "symbol": self.symbol,
            "currency": self.currency.value if self.currency else None,
            "market_price": float(self.market_price) if self.market_price else None,
            "shares_outstanding": float(self.shares_outstanding) if self.shares_outstanding else None,
            "float_shares": float(self.float_shares) if self.float_shares else None,
            "market_cap": float(self.market_cap) if self.market_cap else None,
            "calendar": self.calendar.value if self.calendar else None,
            "business_day_convention": self.business_day_convention.value if self.business_day_convention else None,
            "is_active": self.is_active,
            "version": self.version,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def _action_exists(session: Session, action_id: str) -> bool:
        """Check if action ID already exists"""
        return session.query(
            exists().where(CorporateActionHistoryLog.action_id == action_id)
        ).scalar()

    @transaction_rollback
    def rollback_to_state(self, session: Session, log_id: int,
                          rollback_reason: str, rolled_back_by: Optional[str] = None):
        """Rollback to a previous state with enhanced error handling"""

        log_entry = session.query(CorporateActionHistoryLog).filter_by(
            id=log_id, equity_id=self.id).first()

        if not log_entry:
            raise ValueError(f"Log entry {log_id} not found for equity {self.id}")

        if log_entry.is_rolled_back:
            raise ValueError(f"Log entry {log_id} has already been rolled back")

        # Restore state from the log
        state_before = log_entry.state_before
        self._restore_from_state(state_before)

        # Mark the log entry as rolled back
        log_entry.is_rolled_back = True
        log_entry.rolled_back_at = datetime.now()
        log_entry.rolled_back_by = rolled_back_by
        log_entry.rollback_reason = rollback_reason

        self.version += 1
        self.updated_at = datetime.now()

    @transaction_rollback
    @validation_required
    def log_corporate_action(self,
                             session: Session,
                             action_type: CorporateActionTypeEnum,
                             action_parameters: Dict[str, Any],
                             effective_date: datetime,
                             action_id: Optional[str] = None,
                             description: Optional[str] = None,
                             created_by: Optional[str] = None,
                             external_source: Optional[str] = None,
                             confidence_score: Optional[float] = None) -> int:
        """Log corporate action with comprehensive error handling and validation"""

        # Validate inputs
        if not isinstance(effective_date, datetime):
            raise ValueError("effective_date must be a datetime object")

        if action_id and self._action_exists(session, action_id):
            raise ValueError(f"Corporate action {action_id} already logged")

        # Capture state before action
        state_before = self.capture_current_state()

        # Apply the corporate action
        state_after = self.apply_corporate_action(action_type, action_parameters)

        # Create detailed log entry
        log_entry = CorporateActionHistoryLog(
            equity_id=self.id,
            executed_at=datetime.now(),
            effective_date=effective_date,
            action_type=action_type,
            action_id=action_id,
            description=description,
            state_before=state_before,
            state_after=state_after,
            action_parameters=action_parameters,
            created_by=created_by,
            external_source=external_source,
            confidence_score=confidence_score
        )

        session.add(log_entry)
        session.flush()

        # Update version for optimistic locking
        self.version += 1
        self.last_processed_at = datetime.now()

        return log_entry.id

    def get_state_at_date(self, session: Session, target_date: datetime) -> Dict[str, Any]:
        """Get equity state at a specific date"""
        if not isinstance(target_date, datetime):
            raise ValueError("target_date must be a datetime object")

        log = session.query(CorporateActionHistoryLog).filter(
            CorporateActionHistoryLog.equity_id == self.id,
            CorporateActionHistoryLog.effective_date <= target_date,
            CorporateActionHistoryLog.is_rolled_back == False
        ).order_by(CorporateActionHistoryLog.effective_date.desc()).first()

        if log:
            return log.state_after

        return self.capture_current_state()

    def get_pending_actions_chronologically(self, session: Session) -> List['CorporateActionBase']:
        """Get all pending corporate actions in chronological order"""
        from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
        from Equities.corporate_actions.enums.StatusEnum import StatusEnum

        return session.query(CorporateActionBase).filter(
            CorporateActionBase.equity_id == self.id,
            CorporateActionBase.status == StatusEnum.PENDING
        ).order_by(
            CorporateActionBase.execution_date,
            CorporateActionBase.created_at
        ).all()

    def get_history_dataframe(self, session: Session, include_states: bool = True) -> pd.DataFrame:
        """Get corporate action history as DataFrame with memory-efficient processing"""

        query = session.query(CorporateActionHistoryLog).filter_by(
            equity_id=self.id
        ).order_by(CorporateActionHistoryLog.executed_at)

        data = []
        for log in query.yield_per(100):
            row = {
                'log_id': log.id,
                'equity_id': log.equity_id,
                'equity_symbol': self.symbol,
                'executed_at': log.executed_at.isoformat() if log.executed_at else None,
                'effective_date': log.effective_date.isoformat() if log.effective_date else None,
                'action_type': log.action_type.value,
                'action_id': log.action_id,
                'description': log.description,
                'is_rolled_back': log.is_rolled_back,
                'rolled_back_at': log.rolled_back_at.isoformat() if log.rolled_back_at else None,
                'rolled_back_by': log.rolled_back_by,
                'rollback_reason': log.rollback_reason,
                'created_by': log.created_by,
                'external_source': log.external_source,
                'confidence_score': log.confidence_score
            }

            if include_states:
                if log.state_before:
                    row.update({f'before_{k}': v for k, v in log.state_before.items()})
                if log.state_after:
                    row.update({f'after_{k}': v for k, v in log.state_after.items()})
                if log.action_parameters:
                    row.update({f'param_{k}': v for k, v in log.action_parameters.items()})

            data.append(row)

        return pd.DataFrame(data)

    def export_history_to_csv(self, session: Session, filepath: str,
                              include_states: bool = True) -> str:
        """Export history to CSV with directory creation"""

        df = self.get_history_dataframe(session, include_states=include_states)

        base_dir = os.path.dirname(filepath)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)

        df.to_csv(filepath, index=False)
        return filepath
