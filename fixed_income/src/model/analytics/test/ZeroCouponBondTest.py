import math
import unittest
from datetime import date

from fixed_income.src.model.analytics.BondAnalyticsFactory import bond_analytics_factory
from fixed_income.src.model.bonds import BondBase, ZeroCouponBondModel
from fixed_income.src.model.enums import BondTypeEnum, BusinessDayConventionEnum, CalendarEnum, CompoundingEnum, \
    DayCountConventionEnum, FrequencyEnum
from fixed_income.src.model.enums.CurrencyEnum import CurrencyEnum


class ZeroCouponBondTest(unittest.TestCase):
    """Comprehensive test suite for ZeroCouponBondAnalytics"""

    @classmethod
    def setUpClass(cls):
        """Common test data for all tests"""
        cls.base_params = {
            "symbol": "ZCB_TEST",
            "bond_type": BondTypeEnum.ZERO_COUPON,
            "currency": CurrencyEnum.USD,
            "issue_date": date(2023, 1, 1),
            "maturity_date": date(2028, 1, 1),  # 5-year bond
            "evaluation_date": date(2023, 2, 1),
            "face_value": 100.0,
            "market_price": 85.0,
            "day_count_convention": DayCountConventionEnum.ACTUAL_365_FIXED,
            "settlement_days": 2,
            "calendar": CalendarEnum.TARGET,
            "business_day_convention": BusinessDayConventionEnum.FOLLOWING,
            "compounding": CompoundingEnum.COMPOUNDED,
            "frequency": FrequencyEnum.ANNUAL,
            "accrues_interest_flag": False
        }

    def setUp(self):
        """Create fresh bond for each test"""
        self.bond = ZeroCouponBondModel(**self.base_params)
        self.analytics = bond_analytics_factory(self.bond)

    def _create_bond_variant(self, **overrides):
        """Helper to create bond variants with overridden parameters"""
        params = {**self.base_params, **overrides}
        return ZeroCouponBondModel(**params)

    # --- Validation Tests ---
    def test_invalid_input_type(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(BondBase())

    def test_maturity_before_issue(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(self._create_bond_variant(
                issue_date=date(2023, 1, 1),
                maturity_date=date(2022, 1, 1)
            ))

    def test_negative_face_value(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(self._create_bond_variant(face_value=-1000.0))

    # --- Core Functionality Tests ---
    def test_cashflows(self):
        flows = self.analytics.cashflows()
        self.assertEqual(len(flows), 1)
        flow_date, amount = flows[0]
        self.assertEqual(flow_date, date(2028, 1, 3))  # Adjusted for business days
        self.assertEqual(amount, 100.0)

    def test_price_relationships(self):
        clean = self.analytics.clean_price()
        dirty = self.analytics.dirty_price()

        self.assertAlmostEqual(clean, dirty, places=10)  # Should be equal for ZCB
        self.assertTrue(0 < clean < 100)  # Discount bond range

    def test_yield_properties(self):
        ytm = self.analytics.yield_to_maturity()
        ytw = self.analytics.yield_to_worst()

        self.assertEqual(ytm, ytw)  # Should be equal for ZCB
        self.assertTrue(0 < ytm < 0.2)  # Reasonable range

    def test_duration_properties(self):
        macd = self.analytics.macaulay_duration()
        modd = self.analytics.modified_duration()
        simp = self.analytics.simple_duration()

        # For ZCB, Macaulay duration ≈ time to maturity
        expected_duration = (self.base_params["maturity_date"] -
                             self.base_params["evaluation_date"]).days / 365.0
        self.assertAlmostEqual(macd, expected_duration, delta=0.1)
        self.assertLess(modd, macd)  # Modified duration < Macaulay
        self.assertAlmostEqual(simp, macd, delta=0.1)

    def test_convexity(self):
        conv = self.analytics.convexity()
        self.assertTrue(conv > 0)

        # Approximate convexity for ZCB: duration^2 / (1 + ytm)
        duration = self.analytics.macaulay_duration()
        ytm = self.analytics.yield_to_maturity()
        approx_conv = (duration ** 2) / (1 + ytm)
        self.assertAlmostEqual(conv, approx_conv, delta=5)

    # --- Special Case Tests ---
    def test_very_short_maturity(self):
        short_bond = self._create_bond_variant(
            maturity_date=date(2023, 2, 2),
            evaluation_date=date(2023, 2, 1),
            settlement_days=0,
            market_price=99.0
        )
        analytics = bond_analytics_factory(short_bond)
        self.assertAlmostEqual(analytics.macaulay_duration(), 1 / 365, delta=0.001)

    def test_very_long_maturity(self):
        long_bond = self._create_bond_variant(
            maturity_date=date(2053, 1, 1),
            market_price=15.0
        )
        analytics = bond_analytics_factory(long_bond)
        self.assertTrue(analytics.macaulay_duration() > 20)

    def test_high_yield(self):
        high_yield_bond = self._create_bond_variant(market_price=20.0)
        ytm = bond_analytics_factory(high_yield_bond).yield_to_maturity()
        self.assertTrue(ytm > 0.3)

    def test_low_yield(self):
        low_yield_bond = self._create_bond_variant(market_price=98.0)
        ytm = bond_analytics_factory(low_yield_bond).yield_to_maturity()
        self.assertTrue(ytm < 0.01)

    def test_negative_yield(self):
        neg_yield_bond = self._create_bond_variant(market_price=105.0)
        ytm = bond_analytics_factory(neg_yield_bond).yield_to_maturity()
        self.assertTrue(ytm < 0)

    def test_update_evaluation_date(self):
        original_price = self.analytics.clean_price()

        # Move evaluation date forward (closer to maturity)
        new_date = date(2023, 3, 1)  # 1 month later
        self.analytics.update_evaluation_date(new_date)

        # Price should be HIGHER because we're closer to maturity
        # (same yield, less time discounting)
        new_price = self.analytics.clean_price()
        self.assertGreater(new_price, original_price)

        # Duration should be shorter
        new_duration = self.analytics.macaulay_duration()
        original_duration = (self.base_params["maturity_date"] -
                             self.base_params["evaluation_date"]).days / 365.0
        self.assertLess(new_duration, original_duration)

    def test_holiday_handling(self):
        holiday_bond = self._create_bond_variant(
            maturity_date=date(2023, 12, 25)  # Christmas
        )
        flows = bond_analytics_factory(holiday_bond).cashflows()
        self.assertNotEqual(flows[0][0], date(2023, 12, 25))  # Should adjust

    # --- Error Handling Tests ---
    # @patch.object(bond_analytics_factory(self.bond), 'build_quantlib_bond')
    # def test_error_handling(self, mock_build):
    #     mock_build.side_effect = Exception("Test error")
    #
    #     self.assertEqual(self.analytics.cashflows(), [])
    #     self.assertTrue(math.isnan(self.analytics.clean_price()))

    # --- Additional Suggested Tests ---
    def test_day_count_conventions(self):
        for convention in DayCountConventionEnum:
            bond = self._create_bond_variant(day_count_convention=convention)
            analytics = bond_analytics_factory(bond)
            self.assertFalse(math.isnan(analytics.yield_to_maturity()))

    def test_extreme_price_sensitivity(self):
        # Get current metrics
        dv01 = self.analytics.dv01()
        ytm = self.analytics.yield_to_maturity()
        original_price = self.analytics.clean_price()

        t = (self.bond.maturity_date - self.bond.evaluation_date).days / 365.0
        bumped_price = self.bond.face_value / ((1 + ytm + 0.0001) ** t)

        bumped_bond = self._create_bond_variant(market_price=bumped_price)
        bumped_analytics = bond_analytics_factory(bumped_bond)

        bumped_ytm = bumped_analytics.yield_to_maturity()
        self.assertAlmostEqual(bumped_ytm, ytm + 0.0001, delta=0.00001)


if __name__ == '__main__':
    unittest.main()
