from enum import Enum


class DayCountConventionEnum(str, Enum):
    """
    Enumeration of financial day count conventions with detailed documentation.

    Day count conventions determine how interest accrues over time in financial instruments.
    Each enum value represents a standard market convention with its common applications.

    Members:
        ACTUAL_ACTUAL: "Actual/Actual"
            - Most accurate convention supporting ISDA, ISMA, and Bond subtypes
            - Typical use: Government bonds, treasury securities, highly accurate accruals

        ACTUAL_360: "Actual/360"
            - Common in money market instruments
            - Typical use: Money market instruments, interbank lending, USD Libor-based notes
            - Alias: ACT360

        ACTUAL_365_FIXED: "Actual/365 (Fixed)"
            - Fixed day count using actual days but 365-day year
            - Typical use: UK gilts, corporate bonds, some structured notes
            - Alias: ACT365

        THIRTY_360_US: "30/360 (US Bond Basis)"
            - US corporate bond standard
            - Typical use: US corporates, mortgages, MBS
            - Alias: THIRTY_360

        THIRTY_E_360: "30E/360 (Eurobond Basis)"
            - Eurobond market standard
            - Typical use: Eurobonds, EIB bonds

        THIRTY_E_360_ISDA: "30E/360 (ISDA)"
            - ISDA documentation standard
            - Typical use: Derivatives, ISDA-governed instruments

        BUSINESS_252: "Business/252"
            - Business days-based convention
            - Typical use: Brazilian markets, calendar-based loans

    Full reference table:
        | Convention               | Typical Use Cases                                                  |
        | ------------------------ | ------------------------------------------------------------------ |
        | `Actual/Actual`          | Government bonds, treasury securities, highly accurate accruals    |
        | `Actual/360`             | Money market instruments, interbank lending, USD Libor-based notes |
        | `Actual/365 (Fixed)`     | UK gilts, corporate bonds, some structured notes                   |
        | `30/360 (US Bond Basis)` | US corporates, mortgages, MBS                                      |
        | `30E/360 (Eurobond Basis)`| Eurobonds, EIB bonds                                               |
        | `30E/360 (ISDA)`         | Derivatives, ISDA-governed instruments                             |
        | `Business/252`           | Brazilian markets, calendar-based loans                            |

    Note:
        - Aliases are provided for common alternative naming (e.g., ACT360 for Actual/360)
        - Some conventions have regional or instrument-specific variants
    """

    # Used in bonds, swaps, and many floating-rate instruments; exact treatment varies by submethod
    ACTUAL_ACTUAL = "ACTUAL_ACTUAL"  # Most accurate; supports ISDA, ISMA, Bond subtypes

    # Common in money market instruments (e.g., T-bills, commercial paper, short-term loans)
    ACTUAL_360 = "ACTUAL_360"

    # Used in fixed-income bonds in the UK, corporate bonds, and some international markets
    ACTUAL_365_FIXED = "ACTUAL_365_FIXED"

    # Common in US corporate bonds and agency instruments
    THIRTY_360_US = "THIRTY_360_US"

    # Used in Eurobond markets and international bond documentation
    THIRTY_E_360 = "THIRTY_E_360"

    # Variant used in ISDA documentation (e.g., for some derivatives and swaps)
    THIRTY_E_360_ISDA = "THIRTY_E_360_ISDA"

    # Typically used in Brazil and other emerging markets where calendars drive interest
    BUSINESS_252 = "BUSINESS_252"

    # Aliases (optional, for internal mapping or user input compatibility)
    ACT360 = "ACT360"
    ACT365 = "ACT365"
    THIRTY_360 = "THIRTY_360"
