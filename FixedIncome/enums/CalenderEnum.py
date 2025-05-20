from enum import Enum


class CalendarEnum(str, Enum):
    """
    Enumeration of financial market calendars for business day determination.

    Represents regionally-specific holiday calendars used to determine valid business days
    for trading, settlement, and payment calculations across global financial markets.
    Each calendar incorporates national holidays, market closures, and special observance days.

    Members are organized by geographic region with standardized naming:
    [Country].[InstitutionType] where applicable

    Regional Calendars:
        EUROPE:
            TARGET (TARGET):
                • Eurozone interbank settlement system
                • Covers all TARGET2 operating days
                • Example use: EUR-denominated bond coupon payments

        UNITED STATES:
            US_SETTLEMENT (UnitedStates.Settlement):
                • Standard NY/London banking days
                • Excludes: New Year's Day, Independence Day, etc.
                • Example use: Corporate bond settlements

            US_GOVERNMENT_BOND (UnitedStates.GovernmentBond):
                • Specific to US Treasury market
                • Includes: Columbus Day (unlike corporate calendar)
                • Example use: Treasury auction settlement

            US_NYSE (UnitedStates.NYSE):
                • NYSE trading days
                • Includes: Early closes before holidays
                • Example use: Equity derivative valuations

        UNITED KINGDOM:
            UK_EXCHANGE (UnitedKingdom.Exchange):
                • London Stock Exchange holidays
                • Includes: Spring Bank Holiday, Summer Bank Holiday
                • Example use: UK gilt transactions

        ASIA-PACIFIC:
            CHINA (China):
                • Shanghai/Shenzhen Stock Exchange
                • Includes: Golden Week, Lunar New Year
                • Example use: Dim Sum bond settlements

    Specialized Calendars:
        • GERMANY_EUREX: Eurex derivatives exchange schedule
        • UK_METALS: London Metal Exchange trading days
        • US_FEDERAL_RESERVE: Federal Reserve wire transfer operating days

    Market Coverage Matrix:
        | Calendar                        | Asset Classes Covered                  | Settlement Impact |
        |---------------------------------|----------------------------------------|-------------------|
        | TARGET                          | EUR-denominated bonds, repos, swaps    | T+2 standard      |
        | US_SETTLEMENT                   | Corporate bonds, loans                 | T+1/T+2           |
        | US_GOVERNMENT_BOND              | Treasury securities                    | T+1               |
        | CHINA                           | A-shares, onshore bonds               | T+0/T+1           |
        | UK_EXCHANGE                     | UK equities, gilts                    | T+1               |

    Implementation Notes:
        1. Calendar hierarchies exist (e.g., US_NYSE ⊂ US_SETTLEMENT)
        2. NullCalendar is for theoretical pricing/testing (no holidays)
        3. Regional calendars may have sub-calendars for:
           - Banking vs. trading days
           - Cash vs. derivative markets
           - Physical settlement vs. cash settlement
        4. Combined calendars are often used for cross-border transactions

    Holiday Rule Sources:
        • Local exchange websites
        • ISDA definitions for derivatives
        • Central bank publications
        • Market practice guides (e.g., SIFMA recommendations)
    """
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
