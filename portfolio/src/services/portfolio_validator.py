import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from portfolio.src.api.schemas.portfolio_schema import PortfolioRequest
from portfolio.src.model import Portfolio
from portfolio.src.model.enums import PortfolioStatusEnum
from portfolio.src.services.portfolio_service_config import PortfolioServiceConfig
from portfolio.src.utils.Exceptions import PortfolioValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class PortfolioValidator:
    """Handles all portfolio validation logic"""

    def __init__(self, config: PortfolioServiceConfig):
        self.config = config

    async def validate_creation_request(self, request: PortfolioRequest) -> None:
        """Validate portfolio creation request"""
        validation_result = await self._run_basic_validations(request)
        if not validation_result.is_valid:
            raise PortfolioValidationError("; ".join(validation_result.errors))

        if validation_result.warnings:
            logger.warning(f"Portfolio validation warnings: {', '.join(validation_result.warnings)}")

    async def validate_update_request(self, request: PortfolioRequest, existing_portfolio: Portfolio) -> None:
        """Validate portfolio update request"""
        validation_result = await self._run_update_validations(request, existing_portfolio)
        if not validation_result.is_valid:
            raise PortfolioValidationError("; ".join(validation_result.errors))

        if validation_result.warnings:
            logger.warning(f"Portfolio update warnings: {', '.join(validation_result.warnings)}")

    async def _run_basic_validations(self, request: PortfolioRequest) -> ValidationResult:
        """Perform basic validations on portfolio request"""
        errors = []
        warnings = []

        # Basic field validation
        if not request.symbol or len(request.symbol) < 2:
            errors.append("Portfolio symbol must be at least 2 characters")

        if not request.name or len(request.name) < 3:
            errors.append("Portfolio name must be at least 3 characters")

        if request.total_shares_outstanding and request.total_shares_outstanding <= 0:
            errors.append("Total shares outstanding must be positive")

        # Date validation
        if request.inception_date and request.inception_date > self._get_current_date():
            errors.append("Inception date cannot be in the future")

        # Fee validation
        if request.management_fee and request.management_fee > self.config.MAX_MANAGEMENT_FEE:
            errors.append(f"Management fee cannot exceed {self.config.MAX_MANAGEMENT_FEE * 100}%")

        # Constituent count validation
        total_constituents = len(request.equities or []) + len(request.bonds or [])
        if total_constituents > self.config.MAX_CONSTITUENTS:
            errors.append(f"Portfolio exceeds maximum constituent limit of {self.config.MAX_CONSTITUENTS}")

        # Constituent validation
        if not request.equities and not request.bonds:
            warnings.append("Portfolio has no constituents")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    async def _run_update_validations(self, request: PortfolioRequest,
                                      existing_portfolio: Portfolio) -> ValidationResult:
        """Perform validations specific to portfolio updates"""
        errors = []
        warnings = []

        # Basic field validation
        if request.symbol and len(request.symbol) < 2:
            errors.append("Portfolio symbol must be at least 2 characters")

        if request.name and len(request.name) < 3:
            errors.append("Portfolio name must be at least 3 characters")

        if (request.total_shares_outstanding is not None and
                request.total_shares_outstanding <= 0):
            errors.append("Total shares outstanding must be positive")

        # Date validation
        if (request.inception_date and
                request.inception_date > self._get_current_date()):
            errors.append("Inception date cannot be in the future")

        # Status transition validation
        if request.status and request.status != existing_portfolio.status:
            if existing_portfolio.status == PortfolioStatusEnum.TERMINATED:
                errors.append("Cannot modify a terminated portfolio")
            elif (existing_portfolio.status == PortfolioStatusEnum.ACTIVE and
                  request.status == PortfolioStatusEnum.DRAFT):
                errors.append("Cannot revert an active portfolio to draft status")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_portfolio_weights(self, constituents: List[Dict[str, Any]]) -> None:
        """Validate that portfolio weights sum to approximately 1.0"""
        if not constituents:
            return

        total_weight = sum(Decimal(str(c["weight"])) for c in constituents)

        if abs(total_weight - Decimal("1.0")) > self.config.WEIGHT_TOLERANCE:
            raise PortfolioValidationError(
                f"Portfolio weights sum to {total_weight}, must be within "
                f"{self.config.WEIGHT_TOLERANCE} of 1.0"
            )

    @staticmethod
    def _get_current_date() -> date:
        """Get current UTC date"""
        return datetime.now(timezone.utc).date()
