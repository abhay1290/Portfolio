# import math
# import unittest
# from unittest.mock import patch
#
#
# class TestFixedCouponBondAnalytics(unittest.TestCase):
#     """Comprehensive test suite for FixedCouponBondAnalytics"""
#
#     def setUp(self):
#         """Set up a standard fixed coupon bond for testing"""
#         # Create a standard bond model for most tests
#         self.issue_date = date(2023, 1, 1)
#         self.maturity_date = date(2028, 1, 1)  # 5-year bond
#         self.evaluation_date = date(2023, 6, 1)  # After issue date to have accrued interest
#         self.settlement_days = 2
#         self.face_value = 1000.0
#         self.market_price = 1050.0  # Premium price
#         self.coupon_rate = 0.05  # 5%
#         self.coupon_frequency = FrequencyEnum.SEMIANNUAL
#         self.day_count = DayCountConventionEnum.ACTUAL_365_FIXED
#
#         # Standard bond model to reuse
#         self.bond_model = FixedRateBondModel(
#             symbol="FCB_NORMAL",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=self.market_price,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=self.coupon_rate,
#             coupon_frequency=self.coupon_frequency,
#             redemption_value=100.0
#         )
#
#         self.analytics = bond_analytics_factory(self.bond_model)
#
#     # Basic validation tests
#     def test_init_validates_input_type(self):
#         """Test that initialization validates the input type"""
#         invalid_model = BondBase(
#             symbol="FCB_NORMAL",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=self.market_price,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL
#         )
#         with self.assertRaises(ValueError):
#             bond_analytics_factory(invalid_model)
#
#     def test_validate_inputs_negative_coupon_rate(self):
#         """Test validation catches negative coupon rate"""
#         invalid_model = FixedRateBondModel(
#             symbol="FCB_NORMAL",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=self.market_price,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=-0.05,  # Negative!
#             coupon_frequency=self.coupon_frequency,
#             redemption_value=100.0
#         )
#         with self.assertRaises(ValueError):
#             bond_analytics_factory(invalid_model)
#
#     # Core functionality tests
#     def test_cashflows(self):
#         """Test that cashflows are correctly returned"""
#         flows = self.analytics.cashflows()
#         self.assertEqual(len(flows), 10)  # 10 coupons + principal
#
#         # Verify first coupon
#         first_coupon_date, first_coupon_amount = flows[0]
#         self.assertEqual(first_coupon_date, date(2023, 7, 3))  # Adjusted for business days
#         self.assertAlmostEqual(first_coupon_amount, 25, places=0)  # 5% semi-annual on 1000
#
#         # Verify principal
#         principal_date, principal_amount = flows[-1]
#         self.assertEqual(principal_date, date(2028, 1, 3))  # Adjusted maturity
#         self.assertAlmostEqual(principal_amount, 1025, places=0)
#
#     def test_clean_price(self):
#         """Test clean price calculation"""
#         price = self.analytics.clean_price()
#         self.assertFalse(math.isnan(price))
#         self.assertTrue(900 < price < 1100)  # Reasonable range for our test bond
#
#     def test_dirty_price(self):
#         """Test dirty price calculation"""
#         clean_price = self.analytics.clean_price()
#         dirty_price = self.analytics.dirty_price()
#         accrued = self.analytics.accrued_interest()
#
#         self.assertFalse(math.isnan(dirty_price))
#         self.assertAlmostEqual(dirty_price, clean_price + accrued, places=6)
#
#     def test_accrued_interest(self):
#         """Test accrued interest calculation"""
#         interest = self.analytics.accrued_interest()
#         self.assertFalse(math.isnan(interest))
#         # Should have some accrued interest since evaluation_date is after issue_date
#         self.assertTrue(0 < interest < 25.0)  # Coupon is 25, accrued should be less
#
#     def test_yield_to_maturity(self):
#         """Test yield to maturity calculation"""
#         ytm = self.analytics.yield_to_maturity()
#         self.assertFalse(math.isnan(ytm))
#         # Check YTM is in a reasonable range (less than coupon rate since premium)
#         self.assertTrue(0 < ytm < self.coupon_rate)
#
#     def test_modified_duration(self):
#         """Test modified duration calculation"""
#         duration = self.analytics.modified_duration()
#         self.assertFalse(math.isnan(duration))
#         # Modified duration should be less than maturity for coupon bond
#         years_to_maturity = (self.maturity_date - self.evaluation_date).days / 365.0
#         self.assertTrue(duration < years_to_maturity)
#
#     def test_macaulay_duration(self):
#         """Test Macaulay duration calculation"""
#         duration = self.analytics.macaulay_duration()
#         self.assertFalse(math.isnan(duration))
#         # Should be less than zero-coupon bond of same maturity
#         self.assertTrue(3 < duration < 5)  # Rough estimate for 5-year bond
#
#     def test_convexity(self):
#         """Test convexity calculation"""
#         convexity = self.analytics.convexity()
#         self.assertFalse(math.isnan(convexity))
#         # Convexity should be positive
#         self.assertTrue(convexity > 0)
#
#     # Special fixed-coupon bond tests
#     def test_first_coupon_irregular(self):
#         """Test bond with irregular first coupon period"""
#         irregular_model = FixedRateBondModel(
#             symbol="FCB_IRREGULAR",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=date(2023, 3, 15),  # Not on coupon date
#             maturity_date=date(2028, 3, 15),
#             evaluation_date=date(2023, 6, 1),
#             face_value=1000.0,
#             market_price=1025.0,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=0.05,
#             coupon_frequency=FrequencyEnum.SEMIANNUAL,
#             redemption_value=100.0
#         )
#
#         analytics = bond_analytics_factory(irregular_model)
#         flows = analytics.cashflows()
#         first_coupon_date, first_coupon_amount = flows[0]
#
#         # First coupon amount should be different due to stub period
#         self.assertNotAlmostEqual(first_coupon_amount, 25.0, places=2)
#
#     def test_ex_coupon_period(self):
#         """Test bond with ex-coupon period"""
#         ex_coupon_model = FixedRateBondModel(
#             symbol="FCB_EX_COUPON",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=self.market_price,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=self.coupon_rate,
#             coupon_frequency=self.coupon_frequency,
#             redemption_value=100.0,
#             ex_coupon_days=5,
#             ex_coupon_calendar=CalendarEnum.TARGET
#         )
#
#         analytics = bond_analytics_factory(ex_coupon_model)
#         # Should still return valid results
#         self.assertFalse(math.isnan(analytics.clean_price()))
#
#     # Edge case tests
#     def test_high_coupon_bond(self):
#         """Test bond with very high coupon rate"""
#         high_coupon_model = FixedRateBondModel(
#             symbol="FCB_HIGH_COUPON",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=1500.0,  # High price for high coupon
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=0.15,  # 15%
#             coupon_frequency=self.coupon_frequency,
#             redemption_value=100.0
#         )
#
#         analytics = bond_analytics_factory(high_coupon_model)
#         ytm = analytics.yield_to_maturity()
#         self.assertTrue(0 < ytm < 0.15)  # YTM less than coupon rate for premium bond
#
#     def test_floating_rate_effect(self):
#         """Test behavior when coupon rate approaches zero"""
#         zero_coupon_model = FixedRateBondModel(
#             symbol="FCB_ZERO_COUPON",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=self.issue_date,
#             maturity_date=self.maturity_date,
#             evaluation_date=self.evaluation_date,
#             face_value=self.face_value,
#             market_price=800.0,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=0.001,  # Near zero
#             coupon_frequency=self.coupon_frequency,
#             redemption_value=100.0
#         )
#
#         analytics = bond_analytics_factory(zero_coupon_model)
#         flows = analytics.cashflows()
#         # Coupon payments should be very small
#         for cf_date, cf_amount in flows[:-1]:  # Exclude principal
#             self.assertTrue(cf_amount < 1.0)
#
#     def test_short_first_coupon(self):
#         """Test bond with very short first coupon period"""
#         short_first_model = FixedRateBondModel(
#             symbol="FCB_SHORT_FIRST",
#             bond_type=BondTypeEnum.FIXED_COUPON,
#             currency=CurrencyEnum.USD,
#             issue_date=date(2023, 6, 1),
#             maturity_date=date(2023, 12, 1),  # 6-month bond
#             evaluation_date=date(2023, 6, 2),
#             face_value=1000.0,
#             market_price=1005.0,
#             day_count_convention=self.day_count,
#             settlement_days=self.settlement_days,
#             calendar=CalendarEnum.TARGET,
#             business_day_convention=BusinessDayConventionEnum.FOLLOWING,
#             compounding=CompoundingEnum.COMPOUNDED,
#             frequency=FrequencyEnum.ANNUAL,
#             coupon_rate=0.05,
#             coupon_frequency=FrequencyEnum.SEMIANNUAL,
#             redemption_value=100.0
#         )
#
#         analytics = bond_analytics_factory(short_first_model)
#         flows = analytics.cashflows()
#         self.assertEqual(len(flows), 1)  # One coupon + principal
#         first_coupon_date, first_payment_amount = flows[0]
#         self.assertAlmostEqual(first_payment_amount, 1025.0, places=0)
#
#     # Error handling tests
#     def test_error_handling_in_cashflows(self):
#         """Test error handling in cashflows method"""
#         with patch.object(self.analytics, 'build_quantlib_bond', side_effect=Exception("Test error")):
#             # Should return empty list
#             self.assertEqual(self.analytics.cashflows(), [])
#
#     def test_error_handling_in_clean_price(self):
#         """Test error handling in clean price calculation"""
#         with patch.object(self.analytics, 'build_quantlib_bond', side_effect=Exception("Test error")):
#             # Should return NaN
#             self.assertTrue(math.isnan(self.analytics.clean_price()))
#
#
# if __name__ == '__main__':
#     unittest.main()
#
import unittest
from datetime import date, timedelta

from Currency.CurrencyEnum import CurrencyEnum
from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum
from FixedIncome.enums.CompoundingEnum import CompoundingEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.model.BondBase import BondBase
from FixedIncome.model.FixedRateBondModel import FixedRateBondModel


class TestFixedCouponBondAnalytics(unittest.TestCase):
    """Comprehensive test suite for FixedCouponBondAnalytics"""

    def setUp(self):
        """Set up a standard fixed coupon bond for testing"""
        # Create a standard bond model for most tests
        self.issue_date = date(2023, 1, 1)
        self.maturity_date = date(2028, 1, 1)  # 5-year bond
        self.evaluation_date = date(2023, 6, 1)  # After issue date to have accrued interest
        self.settlement_days = 2
        self.face_value = 1000.0
        self.market_price = 1050.0  # Premium price
        self.coupon_rate = 0.05  # 5%
        self.coupon_frequency = FrequencyEnum.SEMIANNUAL
        self.day_count = DayCountConventionEnum.ACTUAL_365_FIXED

        # Standard bond model to reuse
        self.bond_model = FixedRateBondModel(
            symbol="FCB_NORMAL",
            bond_type=BondTypeEnum.FIXED_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=self.face_value,
            market_price=self.market_price,
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            coupon_rate=self.coupon_rate,
            coupon_frequency=self.coupon_frequency,
            redemption_value=100.0
        )

        self.analytics = bond_analytics_factory(self.bond_model)

    # Basic validation tests
    def test_init_validates_input_type(self):
        """Test that initialization validates the input type"""
        invalid_model = BondBase(
            symbol="FCB_NORMAL",
            bond_type=BondTypeEnum.FIXED_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=self.face_value,
            market_price=self.market_price,
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL
        )
        with self.assertRaises(ValueError):
            bond_analytics_factory(invalid_model)

    # Pricing Tests
    def test_clean_price_at_par(self):
        """Price should be near par when yield = coupon rate"""
        # Create a new bond priced at par
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["market_price"] = self.face_value
        par_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(par_bond)

        # YTM should be close to coupon rate when priced at par
        ytm = analytics.yield_to_maturity()
        self.assertAlmostEqual(ytm, self.coupon_rate, places=2)

    def test_clean_price_at_premium(self):
        """Price should be above par when yield < coupon rate"""
        # Our standard bond is already at premium (1050 > 1000)
        clean_price = self.analytics.clean_price()
        self.assertGreater(clean_price, self.face_value)

        # Verify the yield is indeed lower than coupon rate
        ytm = self.analytics.yield_to_maturity()
        self.assertLess(ytm, self.coupon_rate)

    def test_clean_price_at_discount(self):
        """Price should be below par when yield > coupon rate"""
        # Create a discount bond
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }

        model_dict["market_price"] = 950.0
        discount_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(discount_bond)

        # Verify the yield is higher than coupon rate
        ytm = analytics.yield_to_maturity()
        self.assertGreater(ytm, self.coupon_rate)

    def test_zero_coupon_bond(self):
        """Test pricing of zero coupon bond"""
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["market_price"] = 800.0
        model_dict["coupon_rate"] = 0.0
        model_dict["coupon_frequency"] = FrequencyEnum.ANNUAL

        zero_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(zero_bond)

        # Theoretical price = FV / (1 + y)^n
        years_to_maturity = 4.5  # From evaluation date (2023-6-1) to maturity (2028-1-1)
        ytm = analytics.yield_to_maturity()
        expected_price = self.face_value / ((1 + ytm) ** years_to_maturity)

        self.assertAlmostEqual(analytics.clean_price(), expected_price, delta=5.0)

    # Yield Tests
    def test_ytm_calculation(self):
        """Test YTM calculation consistency with known prices"""
        test_cases = [
            (1050.0, 0.05, 0.03),  # Premium bond, YTM < coupon
            (1000.0, 0.05, 0.05),  # Par bond, YTM = coupon
            (950.0, 0.05, 0.07)  # Discount bond, YTM > coupon
        ]

        for price, coupon, expected_ytm in test_cases:
            model_dict = {
                k: v for k, v in vars(self.bond_model).items()
                if not k.startswith("_")
            }
            model_dict["market_price"] = price
            model_dict["coupon_rate"] = coupon
            test_bond = FixedRateBondModel(**model_dict)

            analytics = bond_analytics_factory(test_bond)
            calculated_ytm = analytics.yield_to_maturity()
            self.assertAlmostEqual(calculated_ytm, expected_ytm, delta=0.01)

    def test_ytm_extreme_cases(self):
        """Test YTM for extreme cases"""
        # Very high yield
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["market_price"] = 500.0
        high_yield_bond = FixedRateBondModel(**model_dict)
        analytics = bond_analytics_factory(high_yield_bond)
        ytm = analytics.yield_to_maturity()
        self.assertGreater(ytm, 0.15)  # Should be very high

        # Near-zero yield
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["market_price"] = self.face_value * 1.5
        low_yield_bond = FixedRateBondModel(**model_dict)
        analytics = bond_analytics_factory(low_yield_bond)
        ytm = analytics.yield_to_maturity()
        self.assertLess(ytm, 0.01)  # Should be near zero

    # Duration and Convexity Tests
    def test_duration_properties(self):
        """Test duration properties"""
        mac_duration = self.analytics.macaulay_duration()
        mod_duration = self.analytics.modified_duration()

        # Macaulay duration should be greater than modified duration
        self.assertGreater(mac_duration, mod_duration)

        # For bonds with higher coupon, duration should be shorter
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["coupon_rate"] = 0.10
        high_coupon_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(high_coupon_bond)
        self.assertLess(analytics.macaulay_duration(), mac_duration)

    def test_convexity_positive(self):
        """Convexity should always be positive for standard bonds"""
        convexity = self.analytics.convexity()
        self.assertGreater(convexity, 0)

        # Zero coupon bond should have higher convexity
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["coupon_rate"] = 0.0
        zero_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(zero_bond)
        self.assertGreater(analytics.convexity(), convexity)

    # Cash Flow Tests
    def test_cash_flows_count(self):
        """Verify correct number of cash flows"""
        cashflows = self.analytics.cashflows()

        # 5-year bond with semiannual coupons = 9 coupon payments + 1 coupon and 1 principal
        self.assertEqual(len(cashflows), 10)

        # Check principal is last payment
        self.assertAlmostEqual(cashflows[-1][1], self.face_value + 25.0, places=0)

    def test_cash_flow_dates(self):
        """Verify cash flow dates are correct"""
        cashflows = self.analytics.cashflows()
        dates = [cf[0] for cf in cashflows]

        # Should be in ascending order
        for i in range(1, len(dates)):
            self.assertLess(dates[i - 1], dates[i])

        # First coupon date should be ~6 months from issue
        first_coupon = dates[0]
        expected_first_coupon = date(2023, 7, 3)  # Semiannual from Jan 1 + accounting for business days
        self.assertEqual(first_coupon, expected_first_coupon)

    # Extreme Scenario Tests
    def test_very_long_maturity(self):
        """Test 100-year bond (century bond)"""
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }
        model_dict["maturity_date"] = date(2123, 1, 1)
        model_dict["coupon_rate"] = 0.04
        model_dict["coupon_frequency"] = FrequencyEnum.ANNUAL
        century_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(century_bond)

        # Price should approach c/y as maturity becomes very long
        expected_price = (0.04 * self.face_value) / analytics.yield_to_maturity()
        self.assertAlmostEqual(analytics.clean_price(), expected_price, delta=self.face_value * 0.3)

    def test_very_high_coupon(self):
        """Test bond with coupon rate near 100%"""

        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }

        model_dict["coupon_rate"] = 0.99
        model_dict["coupon_frequency"] = FrequencyEnum.ANNUAL
        high_coupon_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(high_coupon_bond)

        # Price should be very high since coupons are valuable
        self.assertGreater(analytics.clean_price(), self.face_value * 2)

    def test_very_short_term(self):
        """Test bond maturing in 1 day"""
        model_dict = {
            k: v for k, v in vars(self.bond_model).items()
            if not k.startswith("_")
        }

        model_dict["maturity_date"] = self.evaluation_date + timedelta(days=1)
        model_dict["settlement_days"] = 0
        short_bond = FixedRateBondModel(**model_dict)

        analytics = bond_analytics_factory(short_bond)

        # Price should be very close to face value + last coupon
        self.assertAlmostEqual(analytics.clean_price(), self.face_value, delta=self.face_value * 0.01)

    # Market Price Tests
    def test_market_price_validation(self):
        """Test market price validation"""
        with self.assertRaises(ValueError):
            model_dict = {
                k: v for k, v in vars(self.bond_model).items()
                if not k.startswith("_")
            }
            model_dict["market_price"] = -100
            invalid_bond = FixedRateBondModel(**model_dict)

            bond_analytics_factory(invalid_bond)


if __name__ == '__main__':
    unittest.main()
