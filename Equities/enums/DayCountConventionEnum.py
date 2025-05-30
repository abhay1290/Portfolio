from enum import Enum


class DayCountConventionEnum(str, Enum):
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
