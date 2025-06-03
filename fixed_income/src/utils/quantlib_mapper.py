from datetime import date

from QuantLib import Actual360, Actual365Fixed, ActualActual, Business252, Date, DayCounter, Following, \
    HalfMonthModifiedFollowing, ModifiedFollowing, ModifiedPreceding, Nearest, Period, Preceding, Thirty360, \
    Unadjusted, _QuantLib
from QuantLib import Argentina, Australia, Brazil, Canada, China, France, Germany, HongKong, India, Indonesia, Israel, \
    Japan, Mexico, NewZealand, NullCalendar, SaudiArabia, Singapore, SouthAfrica, SouthKorea, Switzerland, TARGET, \
    Thailand, UnitedKingdom, UnitedStates

from fixed_income.src.model.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from fixed_income.src.model.enums.CalenderEnum import CalendarEnum
from fixed_income.src.model.enums.CompoundingEnum import CompoundingEnum
from fixed_income.src.model.enums.DayCountConventionEnum import DayCountConventionEnum
from fixed_income.src.model.enums.FrequencyEnum import FrequencyEnum


def to_ql_date(d: date | Date) -> Date:
    if isinstance(d, Date):
        return d
    return Date(d.day, d.month, d.year)


def from_ql_date(d: Date | date) -> date:
    if isinstance(d, date):
        return d
    return date(d.year(), d.month(), d.dayOfMonth())


def to_ql_day_count(convention: DayCountConventionEnum) -> DayCounter:
    if convention == DayCountConventionEnum.ACTUAL_ACTUAL:
        return ActualActual(ActualActual.ISDA)
    elif convention in (DayCountConventionEnum.ACTUAL_360, DayCountConventionEnum.ACT360):
        return Actual360()
    elif convention in (DayCountConventionEnum.ACTUAL_365_FIXED, DayCountConventionEnum.ACT365):
        return Actual365Fixed()
    elif convention in (DayCountConventionEnum.THIRTY_360_US, DayCountConventionEnum.THIRTY_360):
        return Thirty360(Thirty360.USA)
    elif convention == DayCountConventionEnum.THIRTY_E_360:
        return Thirty360(Thirty360.European)
    elif convention == DayCountConventionEnum.THIRTY_E_360_ISDA:
        return Thirty360(Thirty360.ISDA)
    elif convention == DayCountConventionEnum.BUSINESS_252:
        return Business252(TARGET())  # Or change to relevant calendar
    else:
        raise ValueError(f"Unsupported Day Count Convention: {convention}")


def to_ql_compounding(compounding_enum: CompoundingEnum) -> int:
    mapping = {
        CompoundingEnum.SIMPLE: 0,
        CompoundingEnum.COMPOUNDED: 1,
        CompoundingEnum.CONTINUOUS: 2,
        CompoundingEnum.SIMPLE_THEN_COMPOUNDED: 3,
        CompoundingEnum.COMPOUNDED_THEN_SIMPLE: 4,
    }
    return mapping[compounding_enum]


def to_ql_frequency(freq_enum: FrequencyEnum) -> Period:
    mapping = {
        FrequencyEnum.NO_FREQUENCY: _QuantLib.NoFrequency,
        FrequencyEnum.ONCE: _QuantLib.Once,
        FrequencyEnum.ANNUAL: _QuantLib.Annual,
        FrequencyEnum.SEMIANNUAL: _QuantLib.Semiannual,
        FrequencyEnum.QUARTERLY: _QuantLib.Quarterly,
        FrequencyEnum.MONTHLY: _QuantLib.Monthly,
        FrequencyEnum.WEEKLY: _QuantLib.Weekly,
        FrequencyEnum.DAILY: _QuantLib.Daily,
        FrequencyEnum.OTHER_FREQUENCY: _QuantLib.OtherFrequency,
    }
    return mapping[freq_enum]


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
