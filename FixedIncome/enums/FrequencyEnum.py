from enum import Enum


class FrequencyEnum(str, Enum):
    """
    Enumeration of payment frequency conventions for financial instruments.

    Defines the temporal distribution of cash flows in debt instruments, derivatives,
    and other financial products. Frequency selection impacts yield calculations,
    duration measurements, and cash flow reinvestment risk.

    Members:
        NO_FREQUENCY (NoFrequency):
            • Single cash flow at maturity
            • Used for: Zero-coupon bonds, bullet repayments
            • Day count impact: Full term accrual
            • Example: 10-year zero-coupon Treasury bond

        ONCE (Once):
            • Single payment at specified date
            • Used for: Lump-sum settlements, spot transactions
            • Distinction from NO_FREQUENCY: Explicit timing specification
            • Example: Forward contract settlement

        ANNUAL (Annual):
            • Yearly payments on anniversary dates
            • Used for: Traditional bonds, annuities
            • Market convention: 1 payment/year
            • Example: Corporate bond with annual coupons

        SEMIANNUAL (Semiannual):
            • Biannual payments (every 6 months)
            • Used for: Most government and corporate bonds
            • Market convention: 30/360 or ACT/ACT accrual
            • Example: US Treasury notes

        QUARTERLY (Quarterly):
            • Quarterly payments (every 3 months)
            • Used for: Floating rate notes, preferred stock
            • Day count impact: ACT/360 common
            • Example: LIBOR-based FRNs

        MONTHLY (Monthly):
            • Monthly payments on same calendar date
            • Used for: Mortgages, retail loans
            • Business day adjustment: Often modified following
            • Example: Residential mortgage payments

        WEEKLY (Weekly):
            • Weekly payments on specified weekday
            • Used for: Short-term commercial paper
            • Settlement: Typically T+1 or T+2
            • Example: Money market fund distributions

        DAILY (Daily):
            • Daily accrual with periodic payment
            • Used for: Overnight repos, cash management
            • Compounding: Usually simple interest
            • Example: SOFR-based cash products

        OTHER_FREQUENCY (OtherFrequency):
            • Custom payment schedule
            • Used for: Structured products, bespoke contracts
            • Requires: Explicit schedule specification
            • Example: Seasoned amortization schedules

    Financial Mathematics:
        | Frequency    | Periods/Year | Compounding Factor            | Yield Conversion Formula       |
        |--------------|--------------|--------------------------------|--------------------------------|
        | NO_FREQUENCY | 0            | 1                              | N/A                            |
        | ANNUAL       | 1            | (1 + r)                        | r_annual = r                   |
        | SEMIANNUAL   | 2            | (1 + r/2)²                     | r_annual = 2[(1 + r)^(1/2) - 1]|
        | QUARTERLY    | 4            | (1 + r/4)⁴                     | r_annual = 4[(1 + r)^(1/4) - 1]|
        | MONTHLY      | 12           | (1 + r/12)¹²                   | r_annual = 12[(1 + r)^(1/12) - 1]|
        | CONTINUOUS   | ∞            | eʳ                             | r_annual = ln(1 + r)           |

    Market Conventions:
        • US Treasuries: Semiannual
        • Eurobonds: Annual
        • Mortgages: Monthly
        • Money Markets: Daily accrual with periodic payment
        • Inflation-Linked: Quarterly (e.g., TIPS)
    """
    NO_FREQUENCY = "NO_FREQUENCY"  # For zero coupon bonds, lump sums
    ONCE = "ONCE"  # Single payment
    ANNUAL = "ANNUAL"  # Yearly
    SEMIANNUAL = "SEMIANNUAL"  # Every 6 months
    QUARTERLY = "QUARTERLY"  # Every 3 months
    MONTHLY = "MONTHLY"  # Every month
    WEEKLY = "WEEKLY"  # Every week
    DAILY = "DAILY"  # Every day
    OTHER_FREQUENCY = "OTHER_FREQUENCY"  # Custom frequency
