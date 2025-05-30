from enum import Enum


class BusinessDayConventionEnum(str, Enum):
    FOLLOWING = "FOLLOWING"  # Move to the next business day (most common)
    MODIFIED_FOLLOWING = "MODIFIED_FOLLOWING"  # Move to next business day unless it crosses month-end, then go back
    PRECEDING = "PRECEDING"  # Move to the previous business day
    MODIFIED_PRECEDING = "MODIFIED_PRECEDING"  # Move to previous business day unless it crosses month-start
    UNADJUSTED = "UNADJUSTED"  # Do not adjust the date
    HALF_MONTH_MODIFIED_FOLLOWING = "HALF_MONTH_MODIFIED_FOLLOWING"  # Only adjust to same half-month
    NEAREST = "NEAREST"  # Move to nearest business day (either before or after)
