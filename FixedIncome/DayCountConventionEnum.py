from enum import Enum

class DayCountConventionEnum(Enum):
    ACTUAL_360 = "Actual/360"
    ACTUAL_365 = "Actual/365"
    THIRTY_360 = "30/360"