from enum import Enum


class BondIdentifierTypeEnum(Enum, str):
    """Bond-specific identifier types"""

    # Standard identifiers (reuse from base)
    ISIN = "ISIN"
    CUSIP = "CUSIP"
    SEDOL = "SEDOL"
    WKN = "WKN"
    BLOOMBERG_TICKER = "BLOOMBERG_TICKER"
    REUTERS_RIC = "REUTERS_RIC"
    FIGI = "FIGI"

    # Bond-specific identifiers
    RATING_MOODY = "RATING_MOODY"
    RATING_SP = "RATING_SP"
    RATING_FITCH = "RATING_FITCH"
    CUSIP_INTERNATIONAL = "CUSIP_INTERNATIONAL"
    COMMON_CODE = "COMMON_CODE"
    VALOREN = "VALOREN"

    # Issue-specific
    ISSUE_CODE = "ISSUE_CODE"
    SERIES_CODE = "SERIES_CODE"
