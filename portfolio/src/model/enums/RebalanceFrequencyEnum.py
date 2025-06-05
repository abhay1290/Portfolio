from enum import Enum


class RebalanceFrequencyEnum(str, Enum):
    """Frequency at which portfolio rebalancing occurs"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BI_WEEKLY = "BI_WEEKLY"
    MONTHLY = "MONTHLY"
    BI_MONTHLY = "BI_MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUALLY = "SEMI_ANNUALLY"
    ANNUALLY = "ANNUALLY"
    ON_DRIFT = "ON_DRIFT"  # Rebalance when drift exceeds threshold
    ON_DEMAND = "ON_DEMAND"  # Manual rebalancing only
    NEVER = "NEVER"  # Buy and hold strategy
