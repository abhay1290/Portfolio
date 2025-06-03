import math
import unittest
from datetime import date, timedelta

from Currency.CurrencyEnum import CurrencyEnum
from fixed_income.src.model.analytics.BondAnalyticsFactory import bond_analytics_factory
from fixed_income.src.model.bonds import BondBase, FixedRateBondModel
from fixed_income.src.model.enums import BondTypeEnum, BusinessDayConventionEnum, CalendarEnum, CompoundingEnum, \
    DayCountConventionEnum, FrequencyEnum


class TestFixedCouponBondAnalytics(unittest.TestCase):
    """Comprehensive test suite for FixedCouponBondAnalytics"""

    @classmethod
    def setUpClass(cls):
        """Common test data for all tests"""
        cls.standard_params = {
            "symbol": "TEST_BOND",
            "bond_type": BondTypeEnum.FIXED_COUPON,
            "currency": CurrencyEnum.USD,
            "issue_date": date(2023, 1, 1),
            "maturity_date": date(2028, 1, 1),  # 5-year bond
            "evaluation_date": date(2023, 6, 1),
            "face_value": 1000.0,
            "market_price": 1050.0,
            "day_count_convention": DayCountConventionEnum.ACTUAL_365_FIXED,
            "settlement_days": 2,
            "calendar": CalendarEnum.TARGET,
            "business_day_convention": BusinessDayConventionEnum.FOLLOWING,
            "compounding": CompoundingEnum.COMPOUNDED,
            "frequency": FrequencyEnum.ANNUAL,
            "coupon_rate": 0.05,  # 5%
            "coupon_frequency": FrequencyEnum.SEMIANNUAL,
            "redemption_value": 100.0
        }

    def setUp(self):
        """Create fresh bond for each test"""
        self.bond = FixedRateBondModel(**self.standard_params)
        self.analytics = bond_analytics_factory(self.bond)

    def _create_bond_variant(self, **overrides):
        """Helper to create bond variants with overridden parameters"""
        params = {**self.standard_params, **overrides}
        return FixedRateBondModel(**params)

    # --- Validation Tests ---
    def test_invalid_input_type(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(BondBase())

    def test_negative_coupon_rate(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(self._create_bond_variant(coupon_rate=-0.05))

    # --- Core Functionality Tests ---
    def test_cashflows(self):
        flows = self.analytics.cashflows()
        self.assertEqual(len(flows), 10)  # 5 years * 2 coupons/year

        # Verify first coupon
        first_date, first_amount = flows[0]
        self.assertEqual(first_date, date(2023, 7, 3))  # Adjusted for business days
        self.assertAlmostEqual(first_amount, 25, delta=0.5)

        # Verify principal
        last_date, last_amount = flows[-1]
        self.assertEqual(last_date, date(2028, 1, 3))
        self.assertAlmostEqual(last_amount, 1025, delta=0.5)  # Face + last coupon

    def test_price_relationships(self):
        clean = self.analytics.clean_price()
        dirty = self.analytics.dirty_price()
        accrued = self.analytics.accrued_interest()

        self.assertAlmostEqual(dirty, clean + accrued, delta=0.01)
        self.assertTrue(900 < clean < 1100)  # Sanity check

    def test_yield_properties(self):
        ytm = self.analytics.yield_to_maturity()
        self.assertTrue(0 < ytm < self.standard_params["coupon_rate"])  # Premium bond

        # Yield vs price relationship
        discount_bond = self._create_bond_variant(market_price=950)
        discount_ytm = bond_analytics_factory(discount_bond).yield_to_maturity()
        self.assertGreater(discount_ytm, ytm)

    def test_duration_convexity(self):
        md = self.analytics.modified_duration()
        macd = self.analytics.macaulay_duration()
        convexity = self.analytics.convexity()

        self.assertGreater(macd, md)
        self.assertTrue(0 < convexity < 50)  # Reasonable range for 5y bond
        self.assertTrue(3 < macd < 5)  # 5y bond duration

    # --- Special Case Tests ---
    def test_zero_coupon_bond(self):
        zero_bond = self._create_bond_variant(coupon_rate=0, market_price=800)
        analytics = bond_analytics_factory(zero_bond)

        flows = analytics.cashflows()
        self.assertEqual(len(flows), 1)  # Just principal
        self.assertAlmostEqual(flows[0][1], 1000, delta=0.1)

        # Duration should be close to maturity
        self.assertAlmostEqual(analytics.macaulay_duration(), 4.5, delta=0.5)

    def test_irregular_first_coupon(self):
        irregular = self._create_bond_variant(
            issue_date=date(2023, 3, 15),
            maturity_date=date(2028, 3, 15)
        )
        flows = bond_analytics_factory(irregular).cashflows()
        first_amount = flows[0][1]
        self.assertNotAlmostEqual(first_amount, 25, delta=0.1)  # Stub period

    def test_ex_coupon_bond(self):
        ex_bond = self._create_bond_variant(ex_coupon_days=5)
        analytics = bond_analytics_factory(ex_bond)
        self.assertFalse(math.isnan(analytics.clean_price()))

    # --- Extreme Scenario Tests ---
    def test_high_coupon_bond(self):
        high_coupon = self._create_bond_variant(coupon_rate=0.15, market_price=1500)
        ytm = bond_analytics_factory(high_coupon).yield_to_maturity()
        self.assertTrue(0 < ytm < 0.15)

    def test_very_short_term(self):
        short_bond = self._create_bond_variant(
            maturity_date=self.standard_params["evaluation_date"] + timedelta(days=1),
            settlement_days=0
        )
        price = bond_analytics_factory(short_bond).clean_price()
        self.assertAlmostEqual(price, 1000, delta=10)

    def test_century_bond(self):
        century = self._create_bond_variant(
            maturity_date=date(2123, 1, 1),
            coupon_rate=0.04
        )
        analytics = bond_analytics_factory(century)
        self.assertTrue(analytics.macaulay_duration() > 20)

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
            self.assertFalse(math.isnan(analytics.accrued_interest()))

    def test_holiday_handling(self):
        # Test bond maturing on holiday
        holiday_bond = self._create_bond_variant(
            maturity_date=date(2023, 12, 25),  # Christmas
            evaluation_date=date(2023, 12, 20)
        )
        flows = bond_analytics_factory(holiday_bond).cashflows()
        self.assertNotEqual(flows[-1][0], date(2023, 12, 25))  # Should adjust

    # def test_settlement_date_edge_cases(self):
    #     # Same day settlement
    #     instant = self._create_bond_variant(settlement_days=0)
    #     self.assertEqual(
    #         bond_analytics_factory(instant).settlement_date,
    #         self.standard_params["evaluation_date"]
    #     )

    def test_negative_yield(self):
        # Only possible in extraordinary market conditions
        negative_bond = self._create_bond_variant(market_price=1100, coupon_rate=0.01)
        ytm = bond_analytics_factory(negative_bond).yield_to_maturity()
        self.assertLess(ytm, 0)

    def test_very_high_frequency(self):
        monthly = self._create_bond_variant(coupon_frequency=FrequencyEnum.MONTHLY)
        flows = bond_analytics_factory(monthly).cashflows()
        self.assertEqual(len(flows), 56)  # (5y * 12) - 4 from eval date

    def test_price_sensitivity(self):
        # Test that price moves inversely to yield
        original_price = self.analytics.clean_price()
        original_ytm = self.analytics.yield_to_maturity()

        # Simulate yield increase
        up_bond = self._create_bond_variant(market_price=1000)
        new_price = bond_analytics_factory(up_bond).clean_price()
        new_ytm = bond_analytics_factory(up_bond).yield_to_maturity()

        self.assertGreater(new_ytm, original_ytm)
        self.assertEqual(new_price, original_price)


if __name__ == '__main__':
    unittest.main()
