import math
import unittest
from datetime import date, timedelta

from Currency.CurrencyEnum import CurrencyEnum
from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.analytics.utils.quantlib_mapper import from_ql_date
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum
from FixedIncome.enums.CompoundingEnum import CompoundingEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.model.BondBase import BondBase
from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel


class ZeroCouponBondTest(unittest.TestCase):
    """Comprehensive test suite for ZeroCouponBondAnalytics with edge cases and extreme scenarios"""

    def setUp(self):
        """Set up a standard zero coupon bond for testing"""
        # Create a standard bond model for most tests
        self.issue_date = date(2023, 1, 1)
        self.maturity_date = date(2028, 1, 1)  # 5-year bond
        self.evaluation_date = date(2023, 2, 1)
        self.settlement_days = 2
        self.face_value = 1000.0
        self.market_price = 850.0
        self.day_count = DayCountConventionEnum.ACTUAL_365_FIXED

        # Standard bond model to reuse
        self.bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
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
            accrues_interest_flag=False
        )

        self.analytics = bond_analytics_factory(self.bond_model)

    def tearDown(self):
        """Clean up after each test"""
        # Reset any QuantLib global state
        pass

    # Basic validation tests

    def test_init_validates_input_type(self):
        """Test that initialization validates the input type"""
        invalid_model = BondBase(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,  # Wrong bond type
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
            # Not a ZeroCouponBondModel
            bond_analytics_factory(invalid_model)

    def test_validate_inputs_maturity_before_issue(self):
        """Test validation catches maturity date before issue date"""
        invalid_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=date(2023, 1, 1),
            maturity_date=date(2022, 1, 1),  # Before issue date!
            evaluation_date=date(2023, 2, 1),
            face_value=100.0,
            market_price=85.0,
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        with self.assertRaises(ValueError):
            bond_analytics_factory(invalid_model)

    def test_validate_inputs_negative_face_value(self):
        """Test validation catches negative face value"""
        invalid_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=-1000.0,  # Negative!
            market_price=850.0,
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        with self.assertRaises(ValueError):
            bond_analytics_factory(invalid_model)

    def test_validate_inputs_evaluation_before_issue(self):
        """Test validation catches evaluation date before issue date"""
        invalid_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=date(2023, 1, 1),
            maturity_date=date(2028, 1, 1),
            evaluation_date=date(2022, 12, 1),  # Before issue date!
            face_value=1000.0,
            market_price=850.0,
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        with self.assertRaises(ValueError):
            bond_analytics_factory(invalid_model)

        # Core functionality tests

    def test_cashflows(self):
        """Test that cashflows are correctly returned"""
        flows = self.analytics.cashflows()
        self.assertEqual(len(flows), 1)
        flow_date, amount = flows[0]
        self.assertEqual(flow_date, date(2028, 1, 3))  # maturity date + settlement_days
        self.assertEqual(amount, 100.0)  # 100% redemption of face value

    def test_clean_price(self):
        """Test clean price calculation"""
        price = self.analytics.clean_price()
        self.assertFalse(math.isnan(price))
        self.assertTrue(0 < price < 100)  # Normal range for a discount bond

    def test_dirty_price(self):
        """Test dirty price calculation"""
        price = self.analytics.dirty_price()
        self.assertFalse(math.isnan(price))
        self.assertTrue(0 < price < 100)

        # For a zero-coupon bond, dirty price should equal clean price
        # (no accrued interest)
        self.assertAlmostEqual(
            self.analytics.clean_price(),
            self.analytics.dirty_price(),
            places=10
        )

    def test_accrued_interest(self):
        """Test accrued interest calculation"""
        interest = self.analytics.accrued_interest()
        self.assertFalse(math.isnan(interest))
        # Zero-coupon bond should have zero accrued interest
        self.assertAlmostEqual(interest, 0.0, places=10)

    def test_yield_to_maturity(self):
        """Test yield to maturity calculation"""
        ytm = self.analytics.yield_to_maturity()
        self.assertFalse(math.isnan(ytm))
        # Check YTM is in a reasonable range (e.g., between 0% and 20%)
        self.assertTrue(0 < ytm < 0.2)

    def test_yield_to_worst(self):
        """Test yield to worst equals YTM for zero coupon bond"""
        ytm = self.analytics.yield_to_maturity()
        ytw = self.analytics.yield_to_worst()
        self.assertEqual(ytm, ytw)

    def test_modified_duration(self):
        """Test modified duration calculation"""
        duration = self.analytics.modified_duration()
        self.assertFalse(math.isnan(duration))
        # Modified duration should be approximately the time to maturity
        # adjusted by yield for a zero-coupon bond
        years_to_maturity = (self.maturity_date - self.evaluation_date).days / 365.0
        self.assertTrue(duration < years_to_maturity)

    def test_macaulay_duration(self):
        """Test Macaulay duration calculation"""
        duration = self.analytics.macaulay_duration()
        self.assertFalse(math.isnan(duration))
        # For a zero-coupon bond, Macaulay duration equals time to maturity
        years_to_maturity = (self.maturity_date - self.evaluation_date).days / 365.0
        self.assertAlmostEqual(duration, years_to_maturity, places=2)

    def test_simple_duration(self):
        """Test simple duration calculation"""
        duration = self.analytics.simple_duration()
        self.assertFalse(math.isnan(duration))
        # Should be close to Macaulay duration
        self.assertAlmostEqual(
            duration,
            self.analytics.macaulay_duration(),
            places=2
        )

    def test_convexity(self):
        """Test convexity calculation"""
        convexity = self.analytics.convexity()
        self.assertFalse(math.isnan(convexity))
        # Convexity should be positive
        self.assertTrue(convexity > 0)

        # For a zero-coupon bond, convexity is related to duration squared
        duration = self.analytics.macaulay_duration()
        # Approximate relationship: convexity ≈ duration²/(1+YTM)
        ytm = self.analytics.yield_to_maturity()
        approx_convexity = (duration ** 2) / (1 + ytm)
        # Check if within 10% of approximation
        relative_diff = abs(convexity - approx_convexity) / approx_convexity
        self.assertTrue(relative_diff < 0.2)

    def test_get_discount_curve(self):
        """Test discount curve generation"""
        curve = self.analytics.get_discount_curve()
        self.assertTrue(isinstance(curve, dict))
        self.assertTrue(len(curve) > 0)

        # All rates should be positive and within reasonable range
        for date_str, rate in curve.items():
            self.assertTrue(0.045 <= rate <= 0.055)

    def test_summary(self):
        """Test summary method returns all expected metrics"""
        summary = self.analytics.summary()
        expected_keys = [
            'clean_price', 'dirty_price', 'accrued_interest',
            'yield_to_maturity', 'yield_to_worst', 'modified_duration',
            'macaulay_duration', 'simple_duration', 'convexity',
            'dv01', 'cashflows'
        ]

        for key in expected_keys:
            self.assertIn(key, summary)

            # Check for NaN in all numeric results
            if key != 'cashflows':
                self.assertFalse(math.isnan(summary[key]))

    def test_update_yield_curve(self):
        """Test updating yield curve with new rate"""
        original_price = self.analytics.clean_price()

        # Update to a higher yield
        self.analytics.update_yield_curve(0.08)  # 8%
        new_price = self.analytics.clean_price()

        # Higher yield should result in lower price
        self.assertTrue(new_price < original_price)

        # Test invalid rate
        with self.assertRaises(ValueError):
            self.analytics.update_yield_curve(-0.05)  # Negative rate

    def test_update_evaluation_date(self):
        """Test updating evaluation date"""
        original_price = self.analytics.clean_price()
        original_duration = self.analytics.modified_duration()
        original_summary = self.analytics.summary()

        # Update to a later evaluation date
        new_evaluation = self.evaluation_date + timedelta(days=365)  # 1 year later
        self.analytics.update_evaluation_date(new_evaluation)

        new_price = self.analytics.clean_price()
        new_duration = self.analytics.modified_duration()
        new_summary = self.analytics.summary()

        # Later settlement should result in higher price (closer to maturity)
        self.assertTrue(new_price > original_price)

        # Duration should decrease as we move closer to maturity
        self.assertTrue(new_duration < original_duration)

        # Test invalid date
        with self.assertRaises(ValueError):
            invalid_date = date(2022, 1, 1)  # Before issue date
            self.analytics.update_evaluation_date(invalid_date)

    # Edge case tests

    def test_very_short_maturity(self):
        """Test very short maturity (nearly mature bond)"""
        short_bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=date(2023, 1, 1),
            maturity_date=date(2023, 2, 2),  # 1 day after evaluation
            evaluation_date=date(2023, 2, 1),
            face_value=1000.0,
            market_price=999.0,  # Almost face value
            day_count_convention=self.day_count,
            settlement_days=0,  # Immediate settlement for this test
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(short_bond_model)
        summary = analytics.summary()

        # Duration should be very small for nearly-mature bond
        duration = analytics.modified_duration()
        self.assertTrue(duration < 0.1)

    def test_very_long_maturity(self):
        """Test very long maturity (e.g., 30-year zero)"""
        long_bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=date(2023, 1, 1),
            maturity_date=date(2053, 1, 1),  # 30 years
            evaluation_date=date(2023, 2, 1),
            face_value=1000.0,
            market_price=150.0,  # Deep discount
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(long_bond_model)
        summary = analytics.summary()

        # Duration should be high for long-dated bonds
        duration = analytics.modified_duration()
        self.assertTrue(20 < duration < 30)

        # Convexity should be very high
        convexity = analytics.convexity()
        self.assertTrue(convexity > 400)

    def test_very_high_yield(self):
        """Test with very high yield (distressed bond scenario)"""
        # Create a bond priced for very high yield
        distressed_bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=1000.0,
            market_price=200.0,  # Severely distressed price
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(distressed_bond_model)
        summary = analytics.summary()

        # Check that calculations still work
        ytm = analytics.yield_to_maturity()
        self.assertFalse(math.isnan(ytm))

        # YTM should be very high
        self.assertTrue(ytm > 0.3)  # Above 30%

    def test_very_low_yield(self):
        """Test with very low yield (premium bond scenario)"""
        # Create a bond priced for very low yield
        premium_bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=1000.0,
            market_price=980.0,  # Very high price for a 5-year zero
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(premium_bond_model)
        summary = analytics.summary()

        # Check that calculations still work
        ytm = analytics.yield_to_maturity()
        self.assertFalse(math.isnan(ytm))

        # YTM should be very low
        self.assertTrue(ytm < 0.01)  # Below 1%

    def test_exact_par_yield(self):
        """Test with exact par yield (theoretical equilibrium)"""
        # First calculate the price that would give exactly 5% yield
        test_yield = 0.05  # 5%
        years = 5
        theoretical_price = 100 / ((1 + test_yield) ** years)

        par_bond_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=1000.0,
            market_price=theoretical_price * 10,  # Convert percentage to price
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(par_bond_model)
        summary = analytics.summary()

        # Calculated YTM should be very close to our test yield
        ytm = analytics.yield_to_maturity()
        self.assertAlmostEqual(ytm, test_yield, places=2)

    def test_zero_market_price(self):
        """Test with zero market price (extreme distress)"""
        # A bond with zero market price is unusual but theoretically possible
        zero_price_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=1000.0,
            market_price=0.0001,  # Virtually zero price
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(zero_price_model)
        summary = analytics.summary()

        # YTM should be extremely high or potentially infinity
        ytm = analytics.yield_to_maturity()
        self.assertTrue(ytm > 5.0 or math.isinf(ytm))

    def test_market_price_above_face(self):
        """Test with market price above face value (negative yield)"""
        # Some markets have experienced negative yields
        negative_yield_model = ZeroCouponBondModel(
            symbol="ZCB_NORMAL",
            bond_type=BondTypeEnum.ZERO_COUPON,
            currency=CurrencyEnum.USD,
            issue_date=self.issue_date,
            maturity_date=self.maturity_date,
            evaluation_date=self.evaluation_date,
            face_value=1000.0,
            market_price=1050.0,  # Above face value
            day_count_convention=self.day_count,
            settlement_days=self.settlement_days,
            calendar=CalendarEnum.TARGET,
            business_day_convention=BusinessDayConventionEnum.FOLLOWING,
            compounding=CompoundingEnum.COMPOUNDED,
            frequency=FrequencyEnum.ANNUAL,
            accrues_interest_flag=False
        )

        analytics = bond_analytics_factory(negative_yield_model)
        summary = analytics.summary()

        # YTM calculation gives negative yield
        ytm = analytics.yield_to_maturity()
        self.assertTrue(ytm < 0)

    # Error handling tests
    #
    # def test_error_handling_in_cashflows(self):
    #     """Test error handling in cashflows method"""
    #     with patch.object(bond_analytics_factory, 'build_quantlib_bond', side_effect=Exception("Test error")):
    #         # Should return empty list
    #         self.assertEqual(self.analytics.cashflows(), [])
    #
    # def test_error_handling_in_clean_price(self):
    #     """Test error handling in clean price calculation"""
    #     with patch.object(bond_analytics_factory, 'build_quantlib_bond', side_effect=Exception("Test error")):
    #         # Should return NaN
    #         self.assertTrue(math.isnan(self.analytics.clean_price()))
    #
    # def test_error_handling_in_ytm(self):
    #     """Test error handling in YTM calculation"""
    #     with patch.object(ZeroCouponBondAnalytics, 'build_quantlib_bond') as mock_build:
    #         mock_bond = MagicMock()
    #         mock_bond.bondYield.side_effect = Exception("Test error")
    #         mock_build.return_value = mock_bond
    #
    #         # Should return NaN
    #         self.assertTrue(math.isnan(self.analytics.yield_to_maturity()))

    # Performance tests (can be skipped if time-constrained)

    def test_performance_multiple_calculations(self):
        """Test performing multiple calculations in sequence"""
        # Perform a series of calculations
        metrics = [
            self.analytics.clean_price(),
            self.analytics.dirty_price(),
            self.analytics.yield_to_maturity(),
            self.analytics.modified_duration(),
            self.analytics.macaulay_duration(),
            self.analytics.convexity(),
            self.analytics.dv01()
        ]

        # Ensure none are NaN
        for metric in metrics:
            self.assertFalse(math.isnan(metric))

    def test_multiple_evaluation_date_changes(self):
        """Test changing evaluation date multiple times"""
        original_price = self.analytics.clean_price()

        # Change multiple times
        for days in [30, 60, 90, 180, 365]:
            new_date = from_ql_date(self.evaluation_date) + timedelta(days=days)
            self.analytics.update_evaluation_date(new_date)

            # Make sure each calculation still works
            price = self.analytics.clean_price()
            ytm = self.analytics.yield_to_maturity()
            duration = self.analytics.modified_duration()
            summary = self.analytics.summary()

            self.assertFalse(math.isnan(price))
            self.assertFalse(math.isnan(ytm))
            self.assertFalse(math.isnan(duration))


if __name__ == '__main__':
    unittest.main()
