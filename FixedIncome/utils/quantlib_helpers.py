from datetime import date

from QuantLib import *

from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum


def _to_ql_date(d: date) -> Date:
    return Date(d.day, d.month, d.year)


def _to_ql_day_count(dc_enum: DayCountConventionEnum):
    if dc_enum == DayCountConventionEnum.ACTUAL_360:
        return Actual360()
    elif dc_enum == DayCountConventionEnum.ACTUAL_365:
        return ActualActual(ActualActual.ISMA)
    elif dc_enum == DayCountConventionEnum.THIRTY_360:
        return Thirty360()
    return None
