from enum import Enum


class DividendFrequencyEnum(str, Enum):
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"
    ONE_TIME = "ONE_TIME"
    OTHER = "OTHER"
