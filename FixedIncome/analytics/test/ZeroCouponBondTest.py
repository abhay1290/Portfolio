import math
import unittest
from datetime import date, timedelta

from QuantLib import Date

from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel


class TestZeroCouponBondAnalytics(unittest.TestCase):
    def setUp(self):
        # Common bond parameters for normal case
        self.normal_bond = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=82.03,  # Approx for 2% YTM
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2023, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2
        )

    def test_normal_case(self):
        """Test standard 10-year zero coupon bond"""
        analytics = bond_analytics_factory(self.normal_bond)
        summary = analytics.summary()
        print(summary)

        # Price/YTM validation
        self.assertAlmostEqual(summary['clean_price'], 71.5, delta=0.5)
        self.assertAlmostEqual(summary['yield_to_maturity'], 0.03, delta=0.01)

        # Duration checks
        self.assertAlmostEqual(summary['macaulay_duration'], 7.0, delta=0.1)
        self.assertLess(summary['modified_duration'], summary['macaulay_duration'])

        # Convexity should be positive
        self.assertGreater(summary['convexity'], 0)

        # Cashflow should have single payment at maturity
        self.assertEqual(len(summary['cashflows']), 1)
        self.assertEqual(summary['cashflows'][0][1], 100)

    def test_bond_at_issue(self):
        """Test bond on its issue date"""
        bond = ZeroCouponBondModel(
            symbol="ZCB_ISSUE",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=100,  # Typically issued at discount, but test edge case
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2020, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertEqual(summary['accrued_interest'], 0)
        self.assertEqual(summary['clean_price'], summary['dirty_price'])

    def test_bond_at_maturity(self):
        """Test bond on its maturity date"""
        bond = ZeroCouponBondModel(
            symbol="ZCB_MATURITY",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2023, 1, 1),
            market_price=100,  # Should be at par at maturity
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2022, 12, 29),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=1
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertAlmostEqual(summary['clean_price'], 100, delta=0.1)
        self.assertAlmostEqual(summary['yield_to_maturity'], 0)
        self.assertAlmostEqual(summary['macaulay_duration'], 0, delta=0.011)

    def test_extreme_long_term(self):
        """Test 100-year zero coupon bond"""
        bond = ZeroCouponBondModel(
            symbol="ZCB_CENTURY",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2120, 1, 1),
            market_price=5.00,  # Extremely discounted
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2023, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertLess(summary['clean_price'], 10)
        self.assertGreater(summary['macaulay_duration'], 50)
        self.assertGreater(summary['convexity'], 1000)

    def test_extreme_short_term(self):
        """Test bond maturing tomorrow"""
        tomorrow = date.today() + timedelta(days=1)
        bond = ZeroCouponBondModel(
            symbol="ZCB_IMMEDIATE",
            face_value=100,
            issue_date=date.today() - timedelta(days=365),
            maturity_date=tomorrow,
            market_price=99.99,  # Almost at par
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date.today(),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=0
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertAlmostEqual(summary['clean_price'], 99.99, delta=0.01)
        self.assertLess(summary['macaulay_duration'], 0.01)
        self.assertLess(summary['convexity'], 0.01)

    def test_zero_price_edge_case(self):
        """Test pathological case of zero price"""
        bond = ZeroCouponBondModel(
            symbol="ZCB_ZERO_PRICE",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=0.01,  # Near-zero price
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2023, 1, 1),
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2
        )
        analytics = bond_analytics_factory(bond)
        summary = analytics.summary()
        print(summary)

        self.assertAlmostEqual(summary['clean_price'], 0.01, delta=0.001)
        self.assertGreater(summary['yield_to_maturity'], 0.5)  # Extremely high YTM
        self.assertTrue(math.isnan(summary['modified_duration']))  # Should fail to calculate

    def test_holiday_settlement(self):
        """Test settlement date falling on holiday"""
        bond = ZeroCouponBondModel(
            symbol="ZCB_HOLIDAY",
            face_value=100,
            issue_date=date(2020, 1, 1),
            maturity_date=date(2030, 1, 1),
            market_price=82.03,
            bond_type=BondTypeEnum.ZERO_COUPON,
            settlement_date=date(2023, 12, 25),  # Christmas
            day_count_convention=DayCountConventionEnum.ACTUAL_365,
            settlement_days=2
        )
        analytics = bond_analytics_factory(bond)
        # Should adjust to next business day automatically
        self.assertNotEqual(analytics.settlement_date, Date(25, 12, 2023))


if __name__ == '__main__':
    unittest.main()
