from enum import Enum


class IdentifierTypeEnum(Enum, str):
    """Comprehensive enum for all major security identifier types"""

    # Primary Market Identifiers
    TICKER = "TICKER"  # Trading symbol
    ISIN = "ISIN"  # International Securities Identification Number
    CUSIP = "CUSIP"  # Committee on Uniform Securities Identification Procedures
    SEDOL = "SEDOL"  # Stock Exchange Daily Official List
    WKN = "WKN"  # Wertpapierkennnummer (German)
    VALOR = "VALOR"  # Swiss identifier

    # Global Identifiers
    FIGI = "FIGI"  # Financial Instrument Global Identifier
    LEI = "LEI"  # Legal Entity Identifier
    GIIN = "GIIN"  # Global Intermediary Identification Number

    # Data Provider Identifiers
    BLOOMBERG_TICKER = "BLOOMBERG_TICKER"
    BLOOMBERG_FIGI = "BLOOMBERG_FIGI"
    BLOOMBERG_GLOBAL_ID = "BLOOMBERG_GLOBAL_ID"
    REUTERS_RIC = "REUTERS_RIC"  # Reuters Instrument Code
    REFINITIV_PERMID = "REFINITIV_PERMID"  # Refinitiv Permanent Identifier
    FACTSET_ENTITY_ID = "FACTSET_ENTITY_ID"
    MORNINGSTAR_ID = "MORNINGSTAR_ID"

    # Exchange Specific
    LOCAL_CODE = "LOCAL_CODE"  # Local exchange code
    MIC = "MIC"  # Market Identifier Code
    EXCHANGE_SYMBOL = "EXCHANGE_SYMBOL"

    # Regional Identifiers
    CINS = "CINS"  # CUSIP International Numbering System
    COMMON_CODE = "COMMON_CODE"  # Euroclear/Clearstream
    SICOVAM = "SICOVAM"  # French identifier

    # Alternative Identifiers
    CIK = "CIK"  # SEC Central Index Key
    GICS = "GICS"  # Global Industry Classification Standard
    SIC = "SIC"  # Standard Industrial Classification
    NAICS = "NAICS"  # North American Industry Classification System

    # Custom/Internal
    INTERNAL_ID = "INTERNAL_ID"
    CUSTOM = "CUSTOM"
