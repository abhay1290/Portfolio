from enum import Enum


class SinkingFundTypeEnum(str, Enum):
    """
    Enumeration of sinking fund mechanisms for bond principal repayment structures.

    Sinking fund types define how and when an issuer retires portions of a bond's
    principal before maturity. These mechanisms provide investors with principal
    protection while giving issuers flexibility in debt management.

    Members:
        FIXED_AMOUNT (Fixed Amount):
            • Mandatory redemption of specified nominal amounts
            • Example: "$10M must be retired quarterly"
            • Risk: May become burdensome if issuer cash flows decline
            • Common in: Investment-grade corporate bonds

        FIXED_PERCENTAGE (Fixed Percentage):
            • Fixed % of original principal retired periodically
            • Example: "5% of initial principal annually"
            • Benefit: Scales with issue size automatically
            • Common in: Municipal revenue bonds

        VARIABLE_PERCENTAGE (Variable Percentage):
            • Dynamic redemption based on performance triggers
            • Example: "10-20% of EBITDA-linked redemption"
            • Risk: Investor uncertainty about timing
            • Common in: Structured finance products

        SCHEDULED_AMORTIZATION (Scheduled Amortization):
            • Predetermined principal reduction schedule
            • Example: "Equal monthly principal payments"
            • Benefit: Predictable cash flow profile
            • Common in: Mortgage-backed securities

        OPTIONAL_REDEMPTION (Optional Redemption):
            • Issuer discretion on early repayments
            • Example: "Callable at par after 5 years"
            • Risk: Reinvestment risk for investors
            • Common in: High-yield corporate bonds

        BULLET_REDEMPTION (Bullet Redemption):
            • Full principal at maturity only
            • Example: "Zero-coupon bond repayment"
            • Benefit: Maximizes duration for issuers
            • Common in: Sovereign bonds, bank capital instruments

    Industry Standards:
        | Type                     | Investor Protection | Issuer Flexibility | Typical Yield Spread |
        |--------------------------|---------------------|--------------------|----------------------|
        | FIXED_AMOUNT            | High                | Low                | +25-50bps           |
        | FIXED_PERCENTAGE        | Medium-High         | Medium             | +15-40bps           |
        | VARIABLE_PERCENTAGE     | Medium              | High               | +50-100bps          |
        | SCHEDULED_AMORTIZATION  | Highest             | None               | -10-+20bps          |
        | OPTIONAL_REDEMPTION     | Low                 | Highest            | +75-150bps          |
        | BULLET_REDEMPTION       | Lowest              | Highest            | Baseline            |

    Note:
        - Sinking fund provisions typically reduce credit risk but may affect duration
        - Optional redemption features usually require yield premiums
        - Amortizing structures create reinvestment risk for investors
        - Combination structures (e.g. fixed + optional) are common in practice
    """
    FIXED_AMOUNT = "FIXED_AMOUNT"
    FIXED_PERCENTAGE = "FIXED_PERCENTAGE"
    VARIABLE_PERCENTAGE = "VARIABLE_PERCENTAGE"
    SCHEDULED_AMORTIZATION = "SCHEDULED_AMORTIZATION"
    OPTIONAL_REDEMPTION = "OPTIONAL_REDEMPTION"
    BULLET_REDEMPTION = "BULLET_REDEMPTION"
