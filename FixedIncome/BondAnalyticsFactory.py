from datetime import date

from QuantLib import *

from FixedIncome.BondModels import (BondBase, CallableBondModel, FixedRateBondModel, FloatingRateBondModel,
                                    PutableBondModel, ZeroCouponBondModel)
from FixedIncome.BondTypeEnum import BondTypeEnum
from FixedIncome.DayCountConventionEnum import DayCountConventionEnum


def _to_ql_date(d: date) -> Date:
    return Date(d.day, d.month, d.year)


def _convert_day_count(dc_enum: DayCountConventionEnum):
    if dc_enum == DayCountConventionEnum.ACTUAL_360:
        return Actual360()
    elif dc_enum == DayCountConventionEnum.ACTUAL_365:
        return ActualActual()
    elif dc_enum == DayCountConventionEnum.THIRTY_360:
        return Thirty360()


class BondAnalyticsBase:
    def __init__(self, bond: BondBase):
        self.symbol = bond.symbol
        self.face_value = bond.face_value
        self.maturity_date = _to_ql_date(bond.maturity_date)
        self.issue_date = _to_ql_date(bond.issue_date)
        self.market_price = bond.market_price
        self.bond_type = bond.bond_type
        self.settlement_date = _to_ql_date(bond.settlement_date) if bond.settlement_date else self.maturity_date
        self.credit_rating = bond.credit_rating
        self.calendar = TARGET()
        self.convention = Following


def bond_analytics_factory(bond: BondBase) -> BondAnalyticsBase:
    if bond.bond_type == BondTypeEnum.ZERO_COUPON:
        return ZeroCouponBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.FIXED_COUPON:
        return FixedRateBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.CALLABLE:
        return CallableBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.PUTABLE:
        return PutableBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.FLOATING:
        return FloatingRateBondAnalytics(bond)
    else:
        raise ValueError(f"Unsupported bond type: {bond.bond_type}")


class ZeroCouponBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: ZeroCouponBondModel):
        super().__init__(bond)
        self.bond = ZeroCouponBond(
            settlementDays=1,
            calendar=self.calendar,
            faceAmount=self.face_value,
            maturityDate=self.maturity_date,
            paymentConvention=self.convention,
            redemption=100.0,
            issueDate=self.issue_date
        )
        self.discount_curve = YieldTermStructureHandle(
            FlatForward(self.settlement_date, QuoteHandle(SimpleQuote(0.05))))
        self.bond.setPricingEngine(DiscountingBondEngine(self.discount_curve))


class FixedRateBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: FixedRateBondModel):
        super().__init__(bond)
        self.coupon_rate = bond.coupon_rate
        self.frequency = bond.frequency
        self.day_count_convention = _convert_day_count(bond.day_count_convention)
        self.schedule = Schedule(
            self.issue_date,
            self.maturity_date,
            Period(int(12 / bond.frequency.value), Months),
            self.calendar,
            self.convention,
            self.convention,
            DateGeneration.Backward,
            False
        )
        self.discount_curve = YieldTermStructureHandle(
            FlatForward(self.settlement_date, QuoteHandle(SimpleQuote(0.05)), self.day_count_convention)
        )
        self.bond = FixedRateBond(
            settlementDays=1,
            faceAmount=self.face_value,
            schedule=self.schedule,
            coupons=[self.coupon_rate],
            paymentDayCounter=self.day_count_convention,
            paymentConvention=self.convention,
            redemption=100.0,
            issueDate=self.issue_date,
            paymentCalendar=self.calendar
        )


class CallableBondAnalytics(FixedRateBondAnalytics):
    def __init__(self, bond: CallableBondModel):
        super().__init__(bond)
        self.call_schedule = bond.call_schedule
        callability_schedule = CallabilitySchedule()

        for entry in self.call_schedule:
            schedule_date = _to_ql_date(date.fromisoformat(entry["date"]))
            schedule_price = entry["price"]
            callability_schedule.append(Callability(
                BondPrice(schedule_price, BondPrice.Clean),
                Callability.Call,
                schedule_date
            ))
        self.bond = CallableFixedRateBond(
            settlementDays=1,
            faceAmount=self.face_value,
            schedule=self.schedule,
            coupons=[self.coupon_rate],
            dayCounter=self.day_count_convention,
            paymentConvention=self.convention,
            redemption=100.0,
            issueDate=self.issue_date,
            putCallSchedule=callability_schedule
        )
        model = HullWhite(self.discount_curve)
        time_grid = TimeGrid(self.maturity_date, 100)
        engine = TreeCallableFixedRateBondEngine(model, time_grid)
        self.bond.setPricingEngine(engine)


class PutableBondAnalytics(FixedRateBondAnalytics):
    def __init__(self, bond: PutableBondModel):
        super().__init__(bond)
        self.put_schedule = bond.put_schedule
        put_schedule = CallabilitySchedule()

        for entry in self.put_schedule:
            schedule_date = _to_ql_date(date.fromisoformat(entry["date"]))
            schedule_price = entry["price"]
            put_schedule.append(Callability(
                BondPrice(schedule_price, BondPrice.Clean),
                Callability.Put,
                schedule_date
            ))
        self.bond = CallableFixedRateBond(
            settlementDays=1,
            faceAmount=self.face_value,
            schedule=self.schedule,
            coupons=[self.coupon_rate],
            dayCounter=self.day_count_convention,
            paymentConvention=self.convention,
            redemption=100.0,
            issueDate=self.issue_date,
            putCallSchedule=put_schedule
        )
        model = HullWhite(self.discount_curve)
        time_grid = TimeGrid(self.maturity_date, 100)
        engine = TreeCallableFixedRateBondEngine(model, time_grid)
        self.bond.setPricingEngine(engine)


class FloatingRateBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: FloatingRateBondModel):
        super().__init__(bond)
        self.coupon_rate = bond.coupon_rate
        self.frequency = bond.frequency
        self.day_count_convention = _convert_day_count(bond.day_count_convention)
        self.schedule = Schedule(
            self.issue_date,
            self.maturity_date,
            Period(int(12 / self.frequency.value), Months),
            self.calendar,
            self.convention,
            self.convention,
            DateGeneration.Backward,
            False
        )
        self.discount_curve = YieldTermStructureHandle(
            FlatForward(self.settlement_date, QuoteHandle(SimpleQuote(0.05)), self.day_count_convention)
        )
        index = Euribor6M(self.discount_curve)
        self.bond = FloatingRateBond(
            settlementDays=1,
            faceAmount=self.face_value,
            schedule=self.schedule,
            index=index,
            paymentConvention=self.convention,
            fixingDays=2,
            gearings=[1.0],
            spreads=[0.0],
            caps=[],
            floors=[],
            inArrears=False,
            redemption=100.0,
            issueDate=self.issue_date
        )
        self.bond.setPricingEngine(DiscountingBondEngine(self.discount_curve))
