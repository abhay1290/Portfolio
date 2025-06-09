from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey, Index, Integer, NUMERIC, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from portfolio.src.database import Base
from portfolio.src.model.enums import AssetClassEnum, CurrencyEnum


class Constituent(Base):
    __tablename__ = 'constituent'
    __table_args__ = (
        Index('idx_constituent_portfolio', 'portfolio_id'),
        Index('idx_constituent_asset', 'asset_id', 'asset_class'),
        Index('idx_constituent_currency', 'currency'),
        Index('idx_constituent_active', 'is_active'),
        CheckConstraint('weight >= 0 AND weight <= 1', name='check_weight_range'),
        CheckConstraint('target_weight IS NULL OR (target_weight >= 0 AND target_weight <= 1)',
                        name='check_target_weight_range'),
        # Ensure asset_id is required for all asset types
        CheckConstraint('asset_id IS NOT NULL', name='check_asset_id_not_null'),
        # Ensure asset_class is one of the valid values
        CheckConstraint(
            f"asset_class IN ('{AssetClassEnum.EQUITY.value}', '{AssetClassEnum.FIXED_INCOME.value}')",
            name='check_asset_class_valid')
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Portfolio relationship
    portfolio_id = Column(Integer, ForeignKey('portfolio.id'), nullable=False)
    portfolio = relationship("Portfolio", back_populates="constituents")

    # Asset identification (polymorphic)
    asset_id = Column(Integer, nullable=False)  # Can be equity_id or bond_id
    asset_class = Column(Enum(AssetClassEnum), nullable=False)  # EQUITY, BOND, or MULTI_ASSET

    # Asset details
    currency = Column(Enum(CurrencyEnum), nullable=False)
    weight = Column(NUMERIC(precision=10, scale=6), nullable=False)
    target_weight = Column(NUMERIC(precision=10, scale=6), nullable=True)
    units = Column(NUMERIC(precision=20, scale=6), nullable=False)
    market_price = Column(NUMERIC(precision=20, scale=2), nullable=False)

    # Timestamps
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    last_rebalanced_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Additional metadata
    notes = Column(Text, nullable=True)
    custom_fields = Column(JSONB, nullable=True, default=dict)

    def __repr__(self):
        return f"<Constituent(id={self.id}, portfolio={self.portfolio_id}, asset={self.asset_class}:{self.asset_id})>"
