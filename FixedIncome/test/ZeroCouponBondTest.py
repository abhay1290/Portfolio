# import unittest
# from datetime import date
#
# from FixedIncome.BondTypeEnum import BondTypeEnum
# from FixedIncome.DayCountConventionEnum import DayCountConventionEnum
# from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
# from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel
#
#
# class ZeroCouponBondTest(unittest.TestCase):
#
#     # Test case for a standard Zero Coupon Bond
#     def test_standard_zero_coupon_bond(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB001",
#             face_value=100,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),  # 10-year bond
#             market_price=61.03,  # Approx price for 5% YTM 10-year zero coupon
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2023, 1, 1),  # 3 years after issue
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=2
#         )
#         analytics = bond_analytics_factory(bond)
#         summary = analytics.summary()
#
#         # Basic validation checks
#         assert 0.049 < summary['yield_to_maturity'] < 0.051  # Should be ~5%
#         assert 60 < summary['clean_price'] < 62  # Should be ~61.03
#         assert summary['macaulay_duration'] > 6  # Remaining duration
#
#         # Verify discount curve returns expected flat curve
#         discount_curve = analytics.get_discount_curve()
#         assert all(0.049 < rate < 0.051 for rate in discount_curve.values())
#
#     # Test case for Zero Market Price (bond in default)
#     def test_zero_market_price(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB002",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=0,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for Zero Face Value
#     def test_zero_face_value(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB003",
#             face_value=0,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=1000,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for very short maturity (e.g., 1 day)
#     def test_short_maturity(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB004",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2020, 1, 2),
#             market_price=1000,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for very long maturity (e.g., 100 years)
#     def test_long_maturity(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB005",
#             face_value=1000,
#             issue_date=date(1920, 1, 1),
#             maturity_date=date(2020, 1, 1),
#             market_price=1000,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for negative interest rates
#     def test_negative_interest_rate(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB006",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=950,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for a high Yield to Maturity (YTM)
#     def test_high_ytm(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB007",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=100,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for invalid date (maturity date before issue date)
#     def test_invalid_date(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB008",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2019, 12, 31),
#             market_price=1000,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         try:
#             analytics = bond_analytics_factory(bond)
#             print(analytics.summary())
#         except Exception as e:
#             print(f"Error occurred: {e}")
#
#     # Test case for a Premium Bond (Market price > Face value)
#     def test_premium_bond(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB009",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=1100,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#     # Test case for a Discount Bond (Market price < Face value)
#     def test_discount_bond(self):
#         bond = ZeroCouponBondModel(
#             symbol="ZCB010",
#             face_value=1000,
#             issue_date=date(2020, 1, 1),
#             maturity_date=date(2029, 12, 31),
#             market_price=900,
#             bond_type=BondTypeEnum.ZERO_COUPON,
#             settlement_date=date(2020, 1, 1),
#             day_count_convention=DayCountConventionEnum.ACTUAL_365,
#             settlement_days=0
#         )
#         analytics = bond_analytics_factory(bond)
#         print(analytics.summary())
#
#
# if __name__ == "__main__":
#     unittest.main()
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
