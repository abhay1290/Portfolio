# Configuration
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class PortfolioServiceConfig:
    """Configuration settings for portfolio service"""
    BATCH_SIZE: int = 50
    DECIMAL_PRECISION: Decimal = Decimal('0.0001')
    PERCENT_PRECISION: Decimal = Decimal('0.01')
    MAX_CONSTITUENTS: int = 1000
    WEIGHT_TOLERANCE: Decimal = Decimal('0.02')  # 2% tolerance
    MAX_WORKERS: int = 4
    MAX_MANAGEMENT_FEE: Decimal = Decimal('0.05')  # 5%
