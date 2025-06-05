from enum import Enum


class RiskLevelEnum(str, Enum):
    """Risk classification levels for portfolios"""
    VERY_LOW = "VERY_LOW"  # Conservative, capital preservation
    LOW = "LOW"  # Low risk, stable income
    MODERATE_LOW = "MODERATE_LOW"  # Slightly conservative
    MODERATE = "MODERATE"  # Balanced risk/return
    MODERATE_HIGH = "MODERATE_HIGH"  # Growth oriented
    HIGH = "HIGH"  # Aggressive growth
    VERY_HIGH = "VERY_HIGH"  # Speculative, high volatility
    EXTREME = "EXTREME"  # Maximum risk tolerance
