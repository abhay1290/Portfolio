from enum import Enum

class IdentifierTypeEnum(Enum):
    TICKER = "Ticker"
    ISIN = "ISIN"
    CUSIP = "CUSIP"
    SEDOL = "SEDOL"
    WKN = "WKN"
    LEI = "LEI"
    FIGI = "FIGI"
    RIC = "RIC"
    MIC = "MIC"
