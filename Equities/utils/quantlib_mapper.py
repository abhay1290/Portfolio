from datetime import date

from QuantLib import Argentina, Australia, Brazil, Canada, China, France, Germany, HongKong, India, Indonesia, Israel, \
    Japan, Mexico, NewZealand, NullCalendar, SaudiArabia, Singapore, SouthAfrica, SouthKorea, Switzerland, TARGET, \
    Thailand, UnitedKingdom, UnitedStates
from QuantLib import Date, Following, \
    HalfMonthModifiedFollowing, ModifiedFollowing, ModifiedPreceding, Nearest, Preceding, Unadjusted

from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum


def to_ql_date(d: date | Date) -> Date:
    if isinstance(d, Date):
        return d
    return Date(d.day, d.month, d.year)


def from_ql_date(d: Date | date) -> date:
    if isinstance(d, date):
        return d
    return date(d.year(), d.month(), d.dayOfMonth())


def to_ql_calendar(calendar_enum: CalendarEnum):
    mapping = {
        CalendarEnum.TARGET: TARGET(),
        CalendarEnum.NULL_CALENDAR: NullCalendar(),

        # United States
        CalendarEnum.US_SETTLEMENT: UnitedStates(UnitedStates.Settlement),
        CalendarEnum.US_GOVERNMENT_BOND: UnitedStates(UnitedStates.GovernmentBond),
        CalendarEnum.US_NYSE: UnitedStates(UnitedStates.NYSE),
        CalendarEnum.US_FEDERAL_RESERVE: UnitedStates(UnitedStates.FederalReserve),

        # United Kingdom
        CalendarEnum.UK_EXCHANGE: UnitedKingdom(UnitedKingdom.Exchange),
        CalendarEnum.UK_SETTLEMENT: UnitedKingdom(UnitedKingdom.Settlement),
        CalendarEnum.UK_METALS: UnitedKingdom(UnitedKingdom.Metals),

        # Germany
        CalendarEnum.GERMANY_FRANKFURT_STOCK_EXCHANGE: Germany(Germany.FrankfurtStockExchange),
        CalendarEnum.GERMANY_EUREX: Germany(Germany.Eurex),
        CalendarEnum.GERMANY_SETTLEMENT: Germany(Germany.Settlement),

        # Others (single variant)
        CalendarEnum.JAPAN: Japan(),
        CalendarEnum.FRANCE: France(),
        CalendarEnum.SWITZERLAND: Switzerland(),
        CalendarEnum.CANADA: Canada(),
        CalendarEnum.MEXICO: Mexico(),
        CalendarEnum.CHINA: China(),
        CalendarEnum.HONG_KONG: HongKong(),
        CalendarEnum.SINGAPORE: Singapore(),
        CalendarEnum.SOUTH_KOREA: SouthKorea(),
        CalendarEnum.INDIA: India(),
        CalendarEnum.INDONESIA: Indonesia(),
        CalendarEnum.THAILAND: Thailand(),
        CalendarEnum.AUSTRALIA: Australia(),
        CalendarEnum.NEW_ZEALAND: NewZealand(),
        CalendarEnum.SAUDI_ARABIA: SaudiArabia(),
        CalendarEnum.ISRAEL: Israel(),
        CalendarEnum.BRAZIL: Brazil(),
        CalendarEnum.ARGENTINA: Argentina(),
        CalendarEnum.SOUTH_AFRICA: SouthAfrica(),
    }

    try:
        return mapping[calendar_enum]
    except KeyError:
        raise ValueError(f"Unsupported CalendarEnum: {calendar_enum}")


def to_ql_business_day_convention(convention_enum: BusinessDayConventionEnum):
    mapping = {
        BusinessDayConventionEnum.FOLLOWING: Following,
        BusinessDayConventionEnum.MODIFIED_FOLLOWING: ModifiedFollowing,
        BusinessDayConventionEnum.PRECEDING: Preceding,
        BusinessDayConventionEnum.MODIFIED_PRECEDING: ModifiedPreceding,
        BusinessDayConventionEnum.UNADJUSTED: Unadjusted,
        BusinessDayConventionEnum.HALF_MONTH_MODIFIED_FOLLOWING: HalfMonthModifiedFollowing,
        BusinessDayConventionEnum.NEAREST: Nearest,
    }
    try:
        return mapping[convention_enum]
    except KeyError:
        raise ValueError(f"Unsupported CalendarEnum: {convention_enum}")
