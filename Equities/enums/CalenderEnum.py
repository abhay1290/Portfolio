from enum import Enum


class CalendarEnum(str, Enum):
    # --- TARGET / Generic ---
    TARGET = "TARGET"  # European interbank calendar (commonly used across Eurozone)

    # --- United States ---
    US_SETTLEMENT = "US_SETTLEMENT"  # Default US settlement calendar
    US_GOVERNMENT_BOND = "US_GOVERNMENT_BOND"  # US Treasury/bond market
    US_NYSE = "US_NYSE"  # NYSE trading calendar
    US_FEDERAL_RESERVE = "US_FEDERAL_RESERVE"  # US Fed-specific banking holidays

    # --- United Kingdom ---
    UK_EXCHANGE = "UK_EXCHANGE"  # London Stock Exchange (LSE)
    UK_SETTLEMENT = "UK_SETTLEMENT"  # General UK settlement calendar
    UK_METALS = "UK_METALS"  # Metals exchange calendar (e.g., LME)

    # --- Germany ---
    GERMANY_FRANKFURT_STOCK_EXCHANGE = "GERMANY_FRANKFURT_STOCK_EXCHANGE"  # Deutsche Börse holidays
    GERMANY_EUREX = "GERMANY_EUREX"  # Eurex derivatives exchange
    GERMANY_SETTLEMENT = "GERMANY_SETTLEMENT"  # General German settlement

    # --- Other major economies (single variant) ---
    JAPAN = "JAPAN"  # General settlement calendar
    FRANCE = "FRANCE"  # Euronext Paris, banks
    SWITZERLAND = "SWITZERLAND"  # SIX Swiss Exchange, banking
    CANADA = "CANADA"  # TSX and Canadian bond markets
    MEXICO = "MEXICO"  # Mexican Exchange and banking

    # --- Asia ---
    CHINA = "CHINA"  # Shanghai/Shenzhen stock exchange
    HONG_KONG = "HONG_KONG"  # HKEX
    SINGAPORE = "SINGAPORE"  # SGX and banks
    SOUTH_KOREA = "SOUTH_KOREA"  # KRX exchange
    INDIA = "INDIA"  # NSE/BSE and RBI
    INDONESIA = "INDONESIA"  # Jakarta Exchange
    THAILAND = "THAILAND"  # Thai markets

    # --- Australia-Pacific ---
    AUSTRALIA = "AUSTRALIA"  # ASX and banks
    NEW_ZEALAND = "NEW_ZEALAND"  # NZX

    # --- Middle East ---
    SAUDI_ARABIA = "SAUDI_ARABIA"  # Tadawul
    ISRAEL = "ISRAEL"  # Tel Aviv Stock Exchange

    # --- South America ---
    BRAZIL = "BRAZIL"  # B3 Exchange
    ARGENTINA = "ARGENTINA"  # Buenos Aires SE

    # --- Africa ---
    SOUTH_AFRICA = "SOUTH_AFRICA"  # Johannesburg SE

    # --- Fallback ---
    NULL_CALENDAR = "NULL_CALENDAR"  # All days are business days (for testing/synthetic instruments)
