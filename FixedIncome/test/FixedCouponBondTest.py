import unittest
from datetime import date, timedelta

from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.CouponFrequencyEnum import CouponFrequencyEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.model.FixedRateBondModel import FixedRateBondModel


class TestFixedCouponBondAnalytics(unittest.TestCase):

    def test_standard_fixed_coupon_bond(self):
        bond = FixedRateBondModel(
            symbol="FCB_STD",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            coupon_rate=0.05,  # 5%
            market_price=950,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertAlmostEqual(summary['yield_to_maturity'], 0.056, delta=0.01)
        self.assertEqual(len(summary['cashflows']), 11)  # 10 years, semi-annual
        self.assertGreater(summary['convexity'], 0)
        self.assertGreater(summary['macaulay_duration'], 0)

    def test_zero_coupon_rate(self):
        bond = FixedRateBondModel(
            symbol="FCB_ZERO_COUPON",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            coupon_rate=0.0,
            market_price=620,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2,
            coupon_frequency=CouponFrequencyEnum.ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertEqual(len(summary['cashflows']), 1)
        self.assertAlmostEqual(summary['yield_to_maturity'], 0.08, delta=0.01)

    def test_premium_bond(self):
        bond = FixedRateBondModel(
            symbol="FCB_PREMIUM",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            coupon_rate=0.07,
            market_price=1080,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertLess(summary['yield_to_maturity'], bond.coupon_rate)
        self.assertGreater(summary['clean_price'], bond.face_value)

    def test_discount_bond(self):
        bond = FixedRateBondModel(
            symbol="FCB_DISCOUNT",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            coupon_rate=0.04,
            market_price=850,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertGreater(summary['yield_to_maturity'], bond.coupon_rate)
        self.assertLess(summary['clean_price'], bond.face_value)

    def test_high_coupon_bond(self):
        bond = FixedRateBondModel(
            symbol="FCB_HIGH_COUPON",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            coupon_rate=0.12,
            market_price=1300,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertLess(summary['yield_to_maturity'], bond.coupon_rate)
        self.assertGreater(summary['clean_price'], bond.face_value)

    def test_bond_at_issue_date(self):
        bond = FixedRateBondModel(
            symbol="FCB_AT_ISSUE",
            face_value=1000,
            issue_date=date(2024, 1, 1),
            maturity_date=date(2034, 1, 1),
            market_price=1000,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2024, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0,
            coupon_rate=0.06,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertEqual(summary['accrued_interest'], 0)

    def test_bond_at_maturity(self):
        bond = FixedRateBondModel(
            symbol="FCB_AT_MATURITY",
            face_value=1000,
            issue_date=date(2010, 1, 1),
            maturity_date=date(2012, 1, 5),
            coupon_rate=0.05,
            market_price=1000,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2012, 1, 4),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0,
            coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertAlmostEqual(summary['macaulay_duration'], 0, delta=0.05)

    def test_long_term_bond(self):
        bond = FixedRateBondModel(
            symbol="FCB_100Y",
            face_value=1000,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2120, 1, 1),
            coupon_rate=0.03,
            market_price=500,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date(2025, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2,
            coupon_frequency=CouponFrequencyEnum.ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertGreater(summary['macaulay_duration'], 40)
        self.assertGreater(len(summary['cashflows']), 90)

    def test_short_term_bond(self):
        maturity = date.today() + timedelta(days=30)
        bond = FixedRateBondModel(
            symbol="FCB_SHORT_TERM",
            face_value=1000,
            issue_date=date.today() - timedelta(days=335),
            maturity_date=maturity,
            coupon_rate=0.03,
            market_price=1000,
            bond_type=BondTypeEnum.FIXED_COUPON,
            settlement_date=date.today(),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0,
            coupon_frequency=CouponFrequencyEnum.ANNUAL,
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertLess(summary['macaulay_duration'], 1)

    def test_invalid_dates(self):
        with self.assertRaises(Exception):
            bond = FixedRateBondModel(
                symbol="FCB_INVALID",
                face_value=1000,
                issue_date=date(2025, 1, 1),
                maturity_date=date(2024, 1, 1),
                coupon_rate=0.05,
                market_price=1000,
                bond_type=BondTypeEnum.FIXED_COUPON,
                settlement_date=date(2025, 1, 1),
                day_count_convention=DayCountConventionEnum.ACTUAL_365,
                settlement_days=0,
                coupon_frequency=CouponFrequencyEnum.SEMI_ANNUAL,
            )
            bond_analytics_factory(bond)


if __name__ == "__main__":
    unittest.main()
