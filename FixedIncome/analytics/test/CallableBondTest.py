import logging
import math
import unittest
from datetime import date
from unittest.mock import Mock, patch

from Currency.CurrencyEnum import CurrencyEnum
from FixedIncome.analytics.BondAnalyticsFactory import bond_analytics_factory
from FixedIncome.analytics.formulation.CallableBondAnalytics import CallableBondAnalytics
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.enums.BusinessDayConventionEnum import BusinessDayConventionEnum
from FixedIncome.enums.CalenderEnum import CalendarEnum
from FixedIncome.enums.CompoundingEnum import CompoundingEnum
from FixedIncome.enums.DayCountConventionEnum import DayCountConventionEnum
from FixedIncome.enums.FrequencyEnum import FrequencyEnum
from FixedIncome.model.BondBase import BondBase
from FixedIncome.model.CallableBondModel import CallableBondModel


class CallableBondAnalyticsTest(unittest.TestCase):
    """Comprehensive test suite for CallableBondAnalytics"""

    @classmethod
    def setUpClass(cls):
        """Common test data for all tests"""
        cls.standard_params = {
            "symbol": "TEST_CALLABLE",
            "bond_type": BondTypeEnum.CALLABLE,
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
            "call_schedule": [
                {"date": "2025-01-01", "price": 102.0},  # Callable at 102% of face
                {"date": "2026-01-01", "price": 101.0},
                {"date": "2027-01-01", "price": 100.0}
            ]
        }

    def setUp(self):
        """Create fresh bond for each test"""
        self.bond = CallableBondModel(**self.standard_params)
        self.analytics = bond_analytics_factory(self.bond)

    def _create_bond_variant(self, **overrides):
        """Helper to create bond variants with overridden parameters"""
        params = {**self.standard_params, **overrides}
        return CallableBondModel(**params)

    # Test Initialization and Validation
    def test_init_with_valid_bond(self):
        analytics = self.analytics
        self.assertIsInstance(analytics, CallableBondAnalytics)
        self.assertEqual(analytics.coupon_rate, 0.05)

    def test_init_with_invalid_bond_type(self):
        with self.assertRaises(ValueError):
            bond_analytics_factory(BondBase())

    def test_validate_negative_settlement_days(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(settlement_days=-1))
        self.assertIn("Settlement days must be a non-negative integer", str(context.exception))

    def test_validate_maturity_before_issue(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(maturity_date=date(2022, 1, 15)))
        self.assertIn("Maturity date must be after issue date", str(context.exception))

    def test_validate_evaluation_after_maturity(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(evaluation_date=date(2029, 1, 15)))
        self.assertIn("Evaluation date is after maturity date", str(context.exception))

    def test_validate_negative_face_value(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(face_value=-1000.0))
        self.assertIn("Face value must be positive", str(context.exception))

    def test_validate_invalid_coupon_rate(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(coupon_rate=-0.01))
        self.assertIn("Coupon rate must be between 0 and 1", str(context.exception))

        # Test coupon rate > 100%

        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(coupon_rate=1.5))
        self.assertIn("Coupon rate must be between 0 and 1", str(context.exception))

    def test_validate_negative_market_price(self):
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(market_price=-100.0))
        self.assertIn("Market price must be positive", str(context.exception))

    # Test Edge Cases for Dates
    def test_zero_settlement_days(self):
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        # Should not raise an error
        self.assertEqual(analytics.settlement_days, 0)

    def test_evaluation_date_equals_issue_date(self):
        """Test edge case where evaluation date equals issue date."""
        analytics = bond_analytics_factory(
            self._create_bond_variant(evaluation_date=date(2023, 1, 1), issue_date=date(2023, 1, 1)))
        # Should not raise an error
        self.assertIsInstance(analytics, CallableBondAnalytics)

    def test_evaluation_date_equals_maturity_date(self):
        """Test edge case where evaluation date equals maturity date."""

        analytics = bond_analytics_factory(
            self._create_bond_variant(evaluation_date=date(2028, 1, 1), maturity_date=date(2028, 1, 1)))
        # Should not raise an error
        self.assertIsInstance(analytics, CallableBondAnalytics)

    # Test Call Schedule Validation
    def test_invalid_call_schedule_format(self):
        """Test validation fails with invalid call schedule format."""
        call_schedule = [
            {"date": "2025-01-15"},  # Missing price
            {"price": 105.0}  # Missing date
        ]
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(call_schedule=call_schedule))
        self.assertIn("Call schedule entries must be dicts with 'date' and 'price' keys", str(context.exception))

    def test_negative_call_price(self):
        """Test validation fails with negative call price."""
        call_schedule = [
            {"date": "2025-01-15", "price": -105.0}
        ]
        with self.assertRaises(ValueError) as context:
            bond_analytics_factory(self._create_bond_variant(call_schedule=call_schedule))
        self.assertIn("Call price must be positive", str(context.exception))

    def test_empty_call_schedule(self):
        """Test handling of empty call schedule."""
        call_schedule = []
        analytics = bond_analytics_factory(self._create_bond_variant(call_schedule=call_schedule))
        # Should not raise an error
        self.assertIsInstance(analytics, CallableBondAnalytics)

    # Test Price Calculations
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_clean_price_calculation(self, mock_build_bond):
        """Test clean price calculation."""
        mock_ql_bond = Mock()
        mock_ql_bond.cleanPrice.return_value = 102.5  # Price per 100
        mock_build_bond.return_value = mock_ql_bond

        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        clean_price = analytics.clean_price()

        # Expected: 102.5 * (1000 / 100) = 1025.0
        self.assertEqual(clean_price, 1025.0)

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_dirty_price_calculation(self, mock_build_bond):
        """Test dirty price calculation."""
        mock_ql_bond = Mock()
        mock_ql_bond.dirtyPrice.return_value = 104.2  # Price per 100
        mock_build_bond.return_value = mock_ql_bond

        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        dirty_price = analytics.dirty_price()

        # Expected: 104.2 * (1000 / 100) = 1042.0
        self.assertEqual(dirty_price, 1042.0)

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_accrued_interest_calculation(self, mock_build_bond):
        """Test accrued interest calculation."""
        mock_ql_bond = Mock()
        mock_ql_bond.accruedAmount.return_value = 1.7  # Accrued per 100
        mock_build_bond.return_value = mock_ql_bond

        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        accrued = analytics.accrued_interest()

        # Expected: 1.7 * (1000 / 100) = 17.0
        self.assertEqual(accrued, 17.0)

    # Test Error Handling in Price Calculations
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_clean_price_calculation_error(self, mock_build_bond):
        """Test clean price calculation handles errors gracefully."""
        mock_build_bond.side_effect = Exception("QuantLib error")

        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        clean_price = analytics.clean_price()

        self.assertTrue(math.isnan(clean_price))

    # Test Yield Calculations
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics._get_normalized_market_price')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_yield_to_maturity_calculation(self, mock_build_bond, mock_normalized_price):
        """Test yield to maturity calculation."""
        mock_ql_bond = Mock()
        mock_ql_bond.bondYield.return_value = 0.045  # 4.5%
        mock_build_bond.return_value = mock_ql_bond
        mock_normalized_price.return_value = 102.0

        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        ytm = analytics.yield_to_maturity()

        self.assertEqual(ytm, 0.045)

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_yield_to_call_no_future_calls(self, mock_build_bond):
        """Test yield to call when no future call dates exist."""
        # Set evaluation date after all call dates

        analytics = bond_analytics_factory(self._create_bond_variant(evaluation_date=date(2028, 1, 16)))
        ytc = analytics.yield_to_call()

        self.assertTrue(math.isnan(ytc))

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_maturity')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_call')
    def test_yield_to_worst_calculation(self, mock_ytc, mock_ytm):
        """Test yield to worst calculation."""
        mock_ytm.return_value = 0.045
        mock_ytc.return_value = 0.040

        analytics = bond_analytics_factory(self.bond)
        ytw = analytics.yield_to_worst()

        # Should return the minimum
        self.assertEqual(ytw, 0.040)

    # Test Duration Calculations
    @patch('QuantLib.BondFunctions.duration')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_maturity')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_modified_duration_calculation(self, mock_build_bond, mock_ytm, mock_duration):
        """Test modified duration calculation."""
        mock_ytm.return_value = 0.045
        mock_duration.return_value = 4.5

        analytics = bond_analytics_factory(self.bond)
        mod_dur = analytics.modified_duration()

        self.assertEqual(mod_dur, 4.5)

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_maturity')
    def test_duration_with_nan_ytm(self, mock_ytm):
        """Test duration calculation when YTM is NaN."""
        mock_ytm.return_value = float('nan')

        analytics = bond_analytics_factory(self.bond)
        mod_dur = analytics.modified_duration()

        self.assertTrue(math.isnan(mod_dur))

    # Test Convexity Calculation
    @patch('QuantLib.BondFunctions.convexity')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_maturity')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_convexity_calculation(self, mock_build_bond, mock_ytm, mock_convexity):
        """Test convexity calculation."""
        mock_ytm.return_value = 0.045
        mock_convexity.return_value = 25.3

        analytics = bond_analytics_factory(self.bond)
        conv = analytics.convexity()

        self.assertEqual(conv, 25.3)

    # Test DV01 Calculation
    @patch('QuantLib.BondFunctions.cleanPrice')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.yield_to_maturity')
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_dv01_calculation(self, mock_build_bond, mock_ytm, mock_clean_price):
        """Test DV01 calculation."""
        mock_ytm.return_value = 0.045
        mock_clean_price.side_effect = [102.45, 101.55]  # price_up, price_down

        analytics = bond_analytics_factory(self.bond)
        dv01 = analytics.dv01()

        # Expected: (101.55 - 102.45) / (2 * 0.0001) = 4500
        expected_dv01 = (101.55 - 102.45) / (2 * 0.0001)
        self.assertEqual(dv01, expected_dv01)

    # Test Cashflow Generation
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.build_quantlib_bond')
    def test_cashflows_generation(self, mock_build_bond):
        """Test cashflow generation."""
        # Mock cashflows
        mock_cf1 = Mock()
        mock_cf1.hasOccurred.return_value = False
        mock_cf1.date.return_value = Mock()
        mock_cf1.amount.return_value = 25.0

        mock_cf2 = Mock()
        mock_cf2.hasOccurred.return_value = False
        mock_cf2.date.return_value = Mock()
        mock_cf2.amount.return_value = 1025.0

        mock_ql_bond = Mock()
        mock_ql_bond.cashflows.return_value = [mock_cf1, mock_cf2]
        mock_build_bond.return_value = mock_ql_bond

        with patch('FixedIncome.analytics.utils.quantlib_mapper.from_ql_date') as mock_from_ql_date:
            mock_from_ql_date.side_effect = [date(2024, 7, 15), date(2025, 1, 15)]

            analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
            cashflows = analytics.cashflows()

            self.assertEqual(len(cashflows), 2)
            self.assertEqual(cashflows[0], (date(2024, 7, 15), 25.0))
            self.assertEqual(cashflows[1], (date(2025, 1, 15), 1025.0))

    def test_cashflows_generation_error(self):
        """Test cashflow generation handles errors gracefully."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with patch.object(analytics, 'build_quantlib_bond', side_effect=Exception("Error")):
            cashflows = analytics.cashflows()
            self.assertEqual(cashflows, [])

    # Test Normalized Market Price
    def test_normalized_market_price_with_market_price(self):
        """Test normalized market price calculation with market price set."""
        analytics = bond_analytics_factory(self._create_bond_variant(market_price=1020.0, settlement_days=0))
        normalized_price = analytics._get_normalized_market_price()

        # Expected: (1020.0 / 1000.0) * 100 = 102.0
        self.assertEqual(normalized_price, 102.0)

    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.CallableBondAnalytics.clean_price')
    def test_normalized_market_price_without_market_price(self, mock_clean_price):
        """Test normalized market price uses clean price as fallback."""

        mock_clean_price.return_value = 1050.0

        analytics = bond_analytics_factory(self._create_bond_variant(market_price=None))
        normalized_price = analytics._get_normalized_market_price()

        # Should use clean price as fallback
        self.assertEqual(normalized_price, 105.0)

    # Test Key Rate Duration
    def test_key_rate_durations_empty_list(self):
        """Test key rate durations with empty key rates list."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with self.assertRaises(ValueError) as context:
            analytics.calculate_key_rate_durations([])
        self.assertIn("Key rates list cannot be empty", str(context.exception))

    def test_key_rate_durations_negative_bump_size(self):
        """Test key rate durations with negative bump size."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with self.assertRaises(ValueError) as context:
            analytics.calculate_key_rate_durations([1, 2, 5], bump_size=-0.0001)
        self.assertIn("Bump size must be positive", str(context.exception))

    def test_key_rate_durations_negative_key_rates(self):
        """Test key rate durations with negative key rates."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with self.assertRaises(ValueError) as context:
            analytics.calculate_key_rate_durations([-1, 2, 5])
        self.assertIn("All key rates must be positive", str(context.exception))

    # Test Curve Updates
    def test_update_yield_curve_invalid_rate(self):
        """Test yield curve update with invalid rate."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with self.assertRaises(ValueError) as context:
            analytics.update_yield_curve(-0.01)
        self.assertIn("Rate must be a non-negative number", str(context.exception))

    def test_update_evaluation_date_before_issue(self):
        """Test evaluation date update before issue date."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with patch('FixedIncome.analytics.utils.quantlib_mapper.to_ql_date') as mock_to_ql_date:
            mock_to_ql_date.return_value = Mock()
            mock_to_ql_date.return_value.__lt__ = Mock(return_value=True)

            with self.assertRaises(ValueError) as context:
                analytics.update_evaluation_date(date(2022, 1, 1))
            self.assertIn("Evaluation date cannot be before Issue date", str(context.exception))

    def test_update_evaluation_date_after_maturity(self):
        """Test evaluation date update after maturity date."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with patch('FixedIncome.analytics.utils.quantlib_mapper.to_ql_date') as mock_to_ql_date:
            mock_to_ql_date.return_value = Mock()
            mock_to_ql_date.return_value.__lt__ = Mock(return_value=False)
            mock_to_ql_date.return_value.__gt__ = Mock(return_value=True)

            with self.assertRaises(ValueError) as context:
                analytics.update_evaluation_date(date(2030, 1, 1))
            self.assertIn("Evaluation date cannot be after Maturity date", str(context.exception))

    # Test Cache Management
    def test_cache_invalidation_on_curve_update(self):
        """Test cache is invalidated when curve is updated."""
        analytics = bond_analytics_factory(self.bond)

        # Set cache
        analytics._summary_cache = {"test": "value"}

        with patch.object(analytics, 'build_quantlib_bond'):
            analytics.update_yield_curve(0.06)

        # Cache should be invalidated
        self.assertIsNone(analytics._summary_cache)

    def test_summary_caching(self):
        """Test summary results are cached."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        # Mock all the calculation methods
        with patch.multiple(analytics,
                            clean_price=Mock(return_value=1025.0),
                            dirty_price=Mock(return_value=1042.0),
                            accrued_interest=Mock(return_value=17.0),
                            yield_to_maturity=Mock(return_value=0.045),
                            yield_to_worst=Mock(return_value=0.040),
                            yield_to_call=Mock(return_value=0.041),
                            modified_duration=Mock(return_value=4.5),
                            macaulay_duration=Mock(return_value=4.7),
                            simple_duration=Mock(return_value=4.6),
                            convexity=Mock(return_value=25.3),
                            dv01=Mock(return_value=0.45),
                            cashflows=Mock(return_value=[]),
                            _get_normalized_market_price=Mock(return_value=102.0)):
            # First call should calculate
            summary1 = analytics.summary()

            # Second call should use cache
            summary2 = analytics.summary()

            # Should be the same object (cached)
            self.assertIs(summary1, summary2)

    # Test Extreme Scenarios
    def test_very_high_coupon_rate(self):
        """Test handling of very high (but valid) coupon rate."""

        analytics = bond_analytics_factory(self._create_bond_variant(coupon_rate=0.99))
        self.assertEqual(analytics.coupon_rate, 0.99)

    def test_zero_coupon_rate(self):
        """Test handling of zero coupon rate."""
        self.mock_bond.coupon_rate = 0.0
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))
        self.assertEqual(analytics.coupon_rate, 0.0)

    def test_very_long_maturity(self):
        """Test handling of very long maturity bond."""
        analytics = bond_analytics_factory(self._create_bond_variant(maturity_date=date(2100, 1, 15)))
        self.assertIsInstance(analytics, CallableBondAnalytics)

    def test_very_short_maturity(self):
        """Test handling of very short maturity bond."""
        analytics = bond_analytics_factory(self._create_bond_variant(issue_date=date(2024, 1, 1),
                                                                     maturity_date=date(2024, 1, 31),
                                                                     evaluation_date=date(2024, 1, 15)))
        self.assertIsInstance(analytics, CallableBondAnalytics)

    def test_very_large_face_value(self):
        """Test handling of very large face value."""
        analytics = bond_analytics_factory(self._create_bond_variant(face_value=1_000_000_000.0))
        self.assertEqual(analytics.face_value, 1_000_000_000.0)

    def test_very_small_face_value(self):
        """Test handling of very small face value."""
        analytics = bond_analytics_factory(self._create_bond_variant(face_value=0.01))
        self.assertEqual(analytics.face_value, 0.01)

    # Test Discount Curve Generation
    def test_discount_curve_invalid_date_range(self):
        """Test discount curve generation with invalid date range."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with patch.object(analytics, 'build_quantlib_bond'):
            curve = analytics.get_discount_curve(
                start=date(2025, 1, 1),
                end=date(2024, 1, 1)  # End before start
            )

            # Should return empty dict due to error
            self.assertEqual(curve, {})

    # Test Logging
    @patch('FixedIncome.analytics.formulation.CallableBondAnalytics.logging')
    def test_error_logging_in_calculations(self, mock_logging):
        """Test that errors are properly logged."""
        analytics = bond_analytics_factory(self._create_bond_variant(settlement_days=0))

        with patch.object(analytics, 'build_quantlib_bond', side_effect=Exception("Test error")):
            result = analytics.clean_price()

            # Should log the error and return NaN
            mock_logging.error.assert_called()
            self.assertTrue(math.isnan(result))

    # Test Call Probability Edge Cases
    def test_call_probability_no_call_schedule(self):
        """Test call probability calculation with no call schedule."""
        analytics = bond_analytics_factory(self._create_bond_variant(call_schedule=[]))

        probabilities = analytics.call_probability()
        self.assertEqual(probabilities, {})

    def test_call_probability_no_future_calls(self):
        """Test call probability calculation with no future call dates."""
        # Set evaluation date after all calls
        analytics = bond_analytics_factory(self._create_bond_variant(evaluation_date=date(2028, 1, 16)))

        probabilities = analytics.call_probability()
        self.assertEqual(probabilities, {})


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)

    # Run tests with detailed output
    unittest.main(verbosity=2)
