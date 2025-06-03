from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, NUMERIC, String, Text

from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase
from equity.src.utils.Exceptions import SpinOffValidationError


class SpinOff(CorporateActionBase):
    __tablename__ = 'spin_off'
    __mapper_args__ = {
        'polymorphic_identity': CorporateActionTypeEnum.SPIN_OFF.value
    }
    API_Path = 'Spin-Off'

    corporate_action_id = Column(Integer, ForeignKey('corporate_action.id', ondelete='CASCADE'), primary_key=True)

    # Spin-off details
    spun_off_equity_id = Column(Integer, ForeignKey('equity.id'), nullable=False)
    spun_off_equity_symbol = Column(String(20), nullable=True)  # Denormalized for easy reference
    distribution_ratio = Column(NUMERIC(precision=10, scale=6), nullable=False)  # New shares per old share
    is_tax_free = Column(Boolean, default=True, nullable=False)  # Section 355 qualification

    # Dates
    announcement_date = Column(Date, nullable=False)
    ex_date = Column(Date, nullable=False)
    distribution_date = Column(Date, nullable=False)
    trading_start_date = Column(Date, nullable=True)  # When spun-off shares start trading

    # Valuation and cost basis
    parent_cost_basis_allocation = Column(NUMERIC(precision=10, scale=6), nullable=True)  # Percentage 0-1
    spinoff_cost_basis_allocation = Column(NUMERIC(precision=10, scale=6), nullable=True)  # Percentage 0-1
    spinoff_fair_value = Column(NUMERIC(precision=20, scale=6), nullable=True)
    parent_price_pre_spinoff = Column(NUMERIC(precision=20, scale=6), nullable=True)
    spinoff_initial_price = Column(NUMERIC(precision=20, scale=6), nullable=True)

    # Fractional share handling
    cash_in_lieu_rate = Column(NUMERIC(precision=20, scale=6), nullable=True)
    fractional_share_rounding = Column(String(20), nullable=True)  # "Round-up", "Round-down", "Cash"

    # Status tracking
    # spinoff_status = Column(Enum(SpinOffStatusEnum), nullable=False, default=SpinOffStatusEnum.ANNOUNCED)

    # Metadata
    spinoff_reason = Column(Text, nullable=True)
    regulatory_approvals = Column(Text, nullable=True)  # JSON string of required approvals
    spinoff_notes = Column(Text, nullable=True)

    def calculate_cost_basis_allocation(self, parent_fv, spinoff_fv):
        """Calculate default cost basis allocation if not provided"""
        if parent_fv and spinoff_fv and parent_fv + spinoff_fv > 0:
            total_value = parent_fv + spinoff_fv
            if self.parent_cost_basis_allocation is None:
                self.parent_cost_basis_allocation = parent_fv / total_value
            if self.spinoff_cost_basis_allocation is None:
                self.spinoff_cost_basis_allocation = spinoff_fv / total_value

    def calculate_implied_value(self, key, parent_post_spinoff_price):
        """Calculate implied value of spin-off based on parent's post-spinoff price"""
        if (parent_post_spinoff_price and self.parent_price_pre_spinoff and
                self.distribution_ratio is not None):
            value_transfer = self.parent_price_pre_spinoff - parent_post_spinoff_price
            self.spinoff_fair_value = value_transfer * self.distribution_ratio

    def validate_cost_basis_sum(self, key, value):
        """Validate that cost basis allocations sum to 1 (if both are provided)"""
        if (self.parent_cost_basis_allocation is not None and
                self.spinoff_cost_basis_allocation is not None):
            total = self.parent_cost_basis_allocation + self.spinoff_cost_basis_allocation
            if abs(total - 1) > 0.0001:  # Allow for small rounding differences
                raise SpinOffValidationError(
                    f"Cost basis allocations must sum to 1 (current sum: {total})"
                )

    def __repr__(self):
        return (
            f"<SpinOff(id={self.corporate_action_id}, "
            f"ratio={self.distribution_ratio}, "
            f"ex_date='{self.ex_date}', "
            f"status='{self.spinoff_status.value}')>"
        )
