from enum import Enum


class DayCountConventionEnum(str, Enum):
    ACTUAL_360 = "ACTUAL_360"
    ACTUAL_365 = "ACTUAL_365"
    THIRTY_360 = "THIRTY_360"
