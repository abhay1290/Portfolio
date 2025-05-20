from enum import Enum


class BusinessDayConventionEnum(str, Enum):
    """
    Enumeration of business day adjustment conventions for financial date calculations.

    Determines how financial dates (coupons, settlements, etc.) are adjusted when they fall
    on weekends or holidays. These rules are critical for cash flow timing, interest accrual,
    and contractual obligations.

    Members:
        FOLLOWING (Following):
            • Adjust to next good business day
            • Impact: Potentially extends accrual periods
            • Market use: ~60% of bond markets (ISDA default)
            • Example: Friday payment date → Monday (if Sat/Sun holiday)
            • Risk: Creates payment delay

        MODIFIED_FOLLOWING (ModifiedFollowing):
            • Follow 'Following' rule unless it crosses month-end
            • Impact: Keeps payments within calendar month
            • Market use: ~30% of bond markets (common in Eurobonds)
            • Example: Jan 31st (Saturday) → Jan 30th (Friday)
            • Benefit: Aligns with accounting periods

        PRECEDING (Preceding):
            • Adjust to previous good business day
            • Impact: Accelerates payment timing
            • Market use: Rare (<5%), some inflation-linked bonds
            • Example: Sunday payment date → Friday
            • Risk: Early payment obligation

        MODIFIED_PRECEDING (ModifiedPreceding):
            • Follow 'Preceding' rule unless it crosses month-start
            • Impact: Keeps payments within calendar month
            • Market use: Very rare (<2%), some MBS structures
            • Example: Feb 1st (Sunday) → Feb 2nd (Monday)
            • Special case: Used for backward-looking instruments

        UNADJUSTED (Unadjusted):
            • No date adjustment (even if non-business day)
            • Impact: Potential settlement failures
            • Market use: Theoretical pricing, some derivatives
            • Example: Contractual date remains Sunday
            • Warning: Requires explicit handling

        HALF_MONTH_MODIFIED_FOLLOWING (HalfMonthModifiedFollowing):
            • Adjust within current half-month period (1-15 or 16-month end)
            • Impact: Constrains payment windows
            • Market use: Japanese bonds, some structured notes
            • Example: Aug 16th (Sunday) → Aug 15th (Friday)
            • Regional: Predominantly Asian markets

        NEAREST (Nearest):
            • Move to closest business day (before/after)
            • Impact: Minimizes day count variation
            • Market use: Some sovereign bonds, inflation swaps
            • Example: Saturday payment → Friday (closer than Monday)
            • Tie-break: Typically follows 'Following' convention

    Adjustment Rule Matrix:
        | Convention                  | Month Boundary | Half-Month | Typical Yield Impact |
        |-----------------------------|----------------|------------|----------------------|
        | FOLLOWING                   | No             | No         | +0-2bps             |
        | MODIFIED_FOLLOWING          | Yes            | No         | ±0bps               |
        | PRECEDING                   | No             | No         | -1-3bps             |
        | MODIFIED_PRECEDING          | Yes            | No         | -0.5-2bps           |
        | HALF_MONTH_MODIFIED_FOLLOWING| Yes           | Yes        | +1-5bps             |
        | NEAREST                     | No             | No         | ±0bps               |

    Implementation Notes:
        1. Modified rules require clear holiday calendar specification
        2. Month boundaries are typically calendar month-end
        3. 'Following' is most liquid convention for derivatives
        4. Unadjusted dates require explicit fail handling procedures
        5. Day count fractions must account for adjusted periods
    """
    FOLLOWING = "FOLLOWING"  # Move to the next business day (most common)
    MODIFIED_FOLLOWING = "MODIFIED_FOLLOWING"  # Move to next business day unless it crosses month-end, then go back
    PRECEDING = "PRECEDING"  # Move to the previous business day
    MODIFIED_PRECEDING = "MODIFIED_PRECEDING"  # Move to previous business day unless it crosses month-start
    UNADJUSTED = "UNADJUSTED"  # Do not adjust the date
    HALF_MONTH_MODIFIED_FOLLOWING = "HALF_MONTH_MODIFIED_FOLLOWING"  # Only adjust to same half-month
    NEAREST = "NEAREST"  # Move to nearest business day (either before or after)
