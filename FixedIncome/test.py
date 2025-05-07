import unittest
from datetime import date

from FixedIncome.BondAnalyticsCalculator import BondAnalyticsCalculator
from FixedIncome.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.BondModels import (CallableBondModel, FixedRateBondModel, FloatingRateBondModel, PutableBondModel,
                                    ZeroCouponBondModel)
from FixedIncome.BondTypeEnum import BondTypeEnum
from FixedIncome.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.DayCountConventionEnum import DayCountConventionEnum


class TestBondAnalytics(unittest.TestCase):

    def test_zero_coupon_bond(self):
        bond = ZeroCouponBondModel(
            symbol="ZCB001",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=600,
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2030, 1, 1)
        )
        analytics = bond_analytics_factory(bond)
        calculator = BondAnalyticsCalculator(analytics)

        print("\nZero Coupon Bond Cals")
        print(f"{calculator.calculate()}")

    def test_fixed_rate_bond(self):
        bond = FixedRateBondModel(
            symbol="FIX001",
            face_value=1000,
            coupon_rate=0.06,
            frequency=CouponFrequencyEnum.SEMI_ANNUAL,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=1200,
            bond_type=BondTypeEnum.FIXED_COUPON,
            day_count_convention=DayCountConventionEnum.ACTUAL_360
        )
        analytics = bond_analytics_factory(bond)
        calculator = BondAnalyticsCalculator(analytics)

        print("\nFixed Rate Bond Analytics")
        print(f"{calculator.calculate()}")

    def test_callable_bond(self):
        bond = CallableBondModel(
            symbol="CALL001",
            face_value=1000,
            coupon_rate=0.05,
            frequency=CouponFrequencyEnum.ANNUAL,
            issue_date=date(2022, 1, 1),
            maturity_date=date(2032, 1, 1),
            market_price=1020,
            bond_type=BondTypeEnum.CALLABLE,
            day_count_convention=DayCountConventionEnum.THIRTY_360,
            call_schedule=[
                {"date": "2027-01-01", "price": 101.0},
                {"date": "2028-01-01", "price": 100.5}
            ]
        )
        analytics = bond_analytics_factory(bond)
        calculator = BondAnalyticsCalculator(analytics)

        print("\nCallable Bond Analytics")
        print(f"{calculator.calculate()}")

    def test_putable_bond(self):
        bond = PutableBondModel(
            symbol="PUT001",
            face_value=1000,
            coupon_rate=0.055,
            frequency=CouponFrequencyEnum.ANNUAL,
            issue_date=date(2021, 1, 1),
            maturity_date=date(2031, 1, 1),
            market_price=990,
            bond_type=BondTypeEnum.PUTABLE,
            day_count_convention=DayCountConventionEnum.ACTUAL_360,
            put_schedule=[
                {"date": "2026-01-01", "price": 99.0},
                {"date": "2027-01-01", "price": 98.0}
            ]
        )
        analytics = bond_analytics_factory(bond)
        calculator = BondAnalyticsCalculator(analytics)

        print("\nPutable Bond Analytics")
        print(f"{calculator.calculate()}")

    def test_floating_rate_bond(self):
        bond = FloatingRateBondModel(
            symbol="FRB001",
            face_value=1000,
            coupon_rate=0.04,
            frequency=CouponFrequencyEnum.SEMI_ANNUAL,
            issue_date=date(2023, 1, 1),
            maturity_date=date(2028, 1, 1),
            market_price=1000,
            bond_type=BondTypeEnum.FLOATING,
            day_count_convention=DayCountConventionEnum.ACTUAL_360,
            reference_index="Euribor6M"
        )
        analytics = bond_analytics_factory(bond)
        calculator = BondAnalyticsCalculator(analytics)

        print("\nFloating Rate Bond Analytics")
        print(f"{calculator.calculate()}")


if __name__ == "__main__":
    unittest.main()
