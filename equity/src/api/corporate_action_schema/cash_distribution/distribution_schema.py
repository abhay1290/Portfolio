from datetime import date
from typing import Optional

from pydantic import ConfigDict, Field, model_validator
from pydantic.types import condecimal, constr

from equity.src.api.corporate_action_schema.corporate_action_schema import CorporateActionRequest, \
    CorporateActionResponse
from equity.src.model.corporate_actions.enums.CorporateActionTypeEnum import CorporateActionTypeEnum


class DistributionRequest(CorporateActionRequest):
    action_type: CorporateActionTypeEnum = Field(default=CorporateActionTypeEnum.DISTRIBUTION, frozen=True,
                                                 description="Type of corporate action")

    # Financial Information
    is_gross_distribution_amount: bool = Field(default=True, description="Whether amount is gross (pre-tax)")
    distribution_amount: condecimal(max_digits=20, decimal_places=6) = Field(..., gt=0)
    eligible_outstanding_shares: float = Field(..., gt=0, description="Number of shares eligible for distribution")

    # Key Dates
    declaration_date: date = Field(..., description="Declaration date")
    ex_distribution_date: Optional[date] = Field(None, description="Ex-distribution date")
    payment_date: date = Field(..., description="Payment date")

    # Tax Information
    distribution_tax_rate: Optional[float] = Field(None, ge=0, le=1, description="Tax rate (0.0 to 1.0)")
    taxable_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)
    non_taxable_amount: Optional[condecimal(max_digits=20, decimal_places=6)] = Field(None, ge=0)

    # Additional Information
    distribution_notes: Optional[constr(max_length=2000)] = Field(None)

    @model_validator(mode='after')
    def validate_tax_related_fields(self) -> 'DistributionRequest':
        if self.distribution_tax_rate is not None and self.distribution_tax_rate > 0:
            if self.taxable_amount is None and self.non_taxable_amount is None:
                raise ValueError("Either taxable_amount or non_taxable_amount must be provided when tax_rate is set")
        return self

    model_config = ConfigDict(extra="forbid")


class DistributionResponse(CorporateActionResponse):
    # Financial Information
    is_gross_distribution_amount: bool
    distribution_amount: float
    eligible_outstanding_shares: float
    net_distribution_amount: Optional[float] = None
    total_distribution_payout: Optional[float] = None

    # Key Dates
    declaration_date: date
    ex_distribution_date: Optional[date] = None
    payment_date: date

    # Tax Information
    distribution_tax_rate: Optional[float] = None
    taxable_amount: Optional[float] = None
    non_taxable_amount: Optional[float] = None

    # Additional Information
    distribution_notes: Optional[str] = None
