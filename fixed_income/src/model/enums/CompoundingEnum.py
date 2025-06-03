from enum import Enum


class CompoundingEnum(str, Enum):
    """
    Enumeration of financial compounding methods with detailed documentation.

    Compounding methods determine how interest is calculated and added to the principal
    over time in financial instruments. Each enum value represents a standard market
    convention with its common applications.

    Members:
        SIMPLE: "Simple"
            - No compounding; interest is not added to the principal
            - Typical use: Short-term instruments, money markets, T-bills

        COMPOUNDED: "Compounded"
            - Interest is compounded periodically (e.g., annually, semiannually)
            - Typical use: Most bonds, loans, deposits, swaps

        CONTINUOUS: "Continuous"
            - Continuous compounding (mathematically elegant)
            - Typical use: Theoretical models, Black-Scholes, yield curve construction

        SIMPLE_THEN_COMPOUNDED: "SimpleThenCompounded"
            - Simple interest initially, then compounded at the end
            - Typical use: Instruments with different accrual styles pre- and post-maturity

        COMPOUNDED_THEN_SIMPLE: "CompoundedThenSimple"
            - Compounded initially, then simple interest
            - Typical use: Special cashflows with staged compounding behavior

    Full reference table:
        | Compounding Method       | Use Case Example                                                 |
        | ------------------------ | ---------------------------------------------------------------- |
        | `Simple`                 | Short-term instruments, money markets, T-bills                   |
        | `Compounded`             | Most bonds, loans, deposits, swaps                               |
        | `Continuous`             | Theoretical models, Black-Scholes, yield curve construction      |
        | `SimpleThenCompounded`   | Instruments with different accrual styles pre- and post-maturity |
        | `CompoundedThenSimple`   | Special cashflows with staged compounding behavior               |

    Note:
        - Simple interest is typically used for instruments with maturities < 1 year
        - Compounded interest is the most common method for longer-term instruments
        - Continuous compounding is primarily used in theoretical finance models
        - Hybrid methods (SimpleThenCompounded/CompoundedThenSimple) are used for
          instruments with complex cashflow structures
    """

    # No compounding; interest is not added to the principal
    SIMPLE = "SIMPLE"

    # Interest is compounded periodically (e.g., annually, semiannually)
    COMPOUNDED = "COMPOUNDED"

    # Continuous compounding (mathematically elegant, often used in theoretical pricing)
    CONTINUOUS = "CONTINUOUS"

    # Interest is compounded, but only at the end (e.g., bullet repayment with accrued interest)
    SIMPLE_THEN_COMPOUNDED = "SIMPLE_THEN_COMPOUNDED"

    # Used when rate changes over time, with partial compounding applied before full compounding
    COMPOUNDED_THEN_SIMPLE = "COMPOUNDED_THEN_SIMPLE"
