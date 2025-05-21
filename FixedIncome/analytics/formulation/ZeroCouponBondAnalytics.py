import logging
import math
from datetime import date
from typing import Dict, List, Optional, Tuple

from QuantLib import (BondFunctions, Days, DiscountingBondEngine, Duration, FlatForward,
                      Period, QuoteHandle, Settings, Simple, SimpleQuote, YieldTermStructureHandle, ZeroCouponBond)

from FixedIncome.analytics.BondAnalyticsFactory import BondAnalyticsBase
from FixedIncome.analytics.utils.helpers import replace_nan_with_none
from FixedIncome.analytics.utils.quantlib_mapper import from_ql_date, to_ql_date
from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel


class ZeroCouponBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: ZeroCouponBondModel):
        super().__init__(bond)

        if not isinstance(bond, ZeroCouponBondModel):
            raise ValueError("Must provide a ZeroCouponBondModel instance")

        self._summary_cache = None

        self._bond: Optional[ZeroCouponBond] = None
        self._discount_curve: Optional[YieldTermStructureHandle] = None
        self._rate_quote: Optional[SimpleQuote] = None

        # Adjust dates to business days
        self._adjust_dates()

        # Global declaration to anchor the calculation point(valuation_date/as_of_date)
        self._set_eval_date_and_settlement_date()
        self._validate_inputs()

    def _adjust_dates(self) -> None:
        """Adjust all relevant dates according to calendar and business day convention."""
        self.evaluation_date = self.calendar.adjust(self.evaluation_date, self.business_day_convention)
        self.maturity_date = self.calendar.adjust(self.maturity_date, self.business_day_convention)

    def _validate_inputs(self) -> None:
        """Validate bond parameters with more comprehensive checks."""
        if not isinstance(self.settlement_days, int) or self.settlement_days < 0:
            raise ValueError("Settlement days must be a non-negative integer")

        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date.")

        if self.settlement_date < self.issue_date:
            raise ValueError("Settlement date cannot be before issue date.")

        if self.face_value <= 0:
            raise ValueError("Face value must be positive.")

        if self.evaluation_date > self.maturity_date:
            raise ValueError("Evaluation date is after maturity date.")

    def _set_eval_date_and_settlement_date(self):
        Settings.instance().evaluationDate = self.evaluation_date
        self.settlement_date = self.calendar.advance(self.evaluation_date, self.settlement_days, Days)
        self.settlement_date = self.calendar.adjust(self.settlement_date, self.business_day_convention)

    def _get_normalized_market_price(self) -> float:
        """Returns market price normalized to 100 face value."""
        market_price = getattr(self, 'market_price', None)
        if market_price is None:
            logging.warning("Market price not set, using clean price as fallback.")
            market_price = self.clean_price()
        if self.face_value == 0:
            raise ZeroDivisionError("Face value cannot be zero when normalizing price.")
        return (market_price / self.face_value) * 100

    # Yield curves must be anchored to the EVALUATION DATE
    def _build_yield_curve(self, initial_rate: float = 0.05) -> Tuple[YieldTermStructureHandle, SimpleQuote]:
        flat_rate = SimpleQuote(initial_rate)
        curve = FlatForward(
            self.evaluation_date,
            QuoteHandle(flat_rate),
            self.day_count_convention,
            self.compounding,
            self.frequency
        )

        curve.enableExtrapolation()  # Allow extrapolation beyond curve dates
        return YieldTermStructureHandle(curve), flat_rate

    def build_quantlib_bond(self) -> ZeroCouponBond:
        if self._bond is None:
            self._bond = ZeroCouponBond(
                settlementDays=self.settlement_days,
                calendar=self.calendar,
                faceAmount=self.face_value,
                maturityDate=self.maturity_date,
                paymentConvention=self.business_day_convention,
                redemption=100.0,
                issueDate=self.issue_date
            )

        if self._discount_curve is None or self._rate_quote is None:
            self._discount_curve, self._rate_quote = self._build_yield_curve()

        engine = DiscountingBondEngine(self._discount_curve)
        self._bond.setPricingEngine(engine)

        return self._bond

    def cashflows(self) -> List[Tuple[date, float]]:
        try:
            bond = self.build_quantlib_bond()
            ql_settlement = to_ql_date(self.settlement_date)
            return [
                (from_ql_date(cf.date()), cf.amount())
                for cf in bond.cashflows()
                if to_ql_date(cf.date()) >= ql_settlement and cf.amount() > 0
            ]
        except Exception as e:
            logging.error(f"Failed to get cashflows: {str(e)}")
            return []

    def clean_price(self) -> float:
        try:
            return self.build_quantlib_bond().cleanPrice()
        except Exception as e:
            logging.error(f"Clean price calculation failed: {str(e)}")
            return float('nan')

    def dirty_price(self) -> float:
        try:
            return self.build_quantlib_bond().dirtyPrice()
        except Exception as e:
            logging.error(f"Dirty price calculation failed: {str(e)}")
            return float('nan')

    def accrued_interest(self) -> float:
        try:
            return self.build_quantlib_bond().accruedAmount()
        except Exception as e:
            logging.error(f"Accrued interest calculation failed: {str(e)}")
            return float('nan')

    def yield_to_maturity(self) -> float:
        try:
            normalized_price = self._get_normalized_market_price()
            return self.build_quantlib_bond().bondYield(
                normalized_price,
                self.day_count_convention,
                self.compounding,
                self.frequency,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"YTM calculation failed: {str(e)}")
            return float('nan')

    def yield_to_worst(self) -> float:
        return self.yield_to_maturity()

    def modified_duration(self) -> float:
        try:
            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')
            return BondFunctions.duration(
                self.build_quantlib_bond(),
                ytm,
                self.day_count_convention,
                self.compounding,
                self.frequency,
                Duration.Modified,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"Modified duration calculation failed: {str(e)}")
            return float('nan')

    def macaulay_duration(self) -> float:
        try:
            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')
            return BondFunctions.duration(
                self.build_quantlib_bond(),
                ytm,
                self.day_count_convention,
                self.compounding,
                self.frequency,
                Duration.Macaulay,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"Macaulay duration calculation failed: {str(e)}")
            return float('nan')

    def simple_duration(self) -> float:
        try:
            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')
            return BondFunctions.duration(
                self.build_quantlib_bond(),
                ytm,
                self.day_count_convention,
                Simple,
                self.frequency,
                Duration.Simple,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"Simple duration calculation failed: {str(e)}")
            return float('nan')

    def convexity(self) -> float:
        try:
            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')
            return BondFunctions.convexity(
                self.build_quantlib_bond(),
                ytm,
                self.day_count_convention,
                self.compounding,
                self.frequency,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"Convexity calculation failed: {str(e)}")
            return float('nan')

    def dv01(self, bump_size: float = 0.0001) -> float:
        try:
            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')

            bond = self.build_quantlib_bond()
            price_up = BondFunctions.cleanPrice(
                bond, ytm + bump_size, self.day_count_convention, self.compounding,
                self.frequency, self.settlement_date
            )
            price_down = BondFunctions.cleanPrice(
                bond, ytm - bump_size, self.day_count_convention, self.compounding,
                self.frequency, self.settlement_date
            )

            return (price_down - price_up) / (2 * bump_size)
        except Exception as e:
            logging.error(f"DV01 calculation failed: {str(e)}")
            return float('nan')

    def get_discount_curve(self, start=None, end=None, points=20) -> Dict[str, float]:
        try:
            if self._discount_curve is None:
                self.build_quantlib_bond()

            curve = self._discount_curve.currentLink()
            calendar = self.calendar
            day_counter = self.day_count_convention
            compounding = self.compounding
            frequency = self.frequency

            ql_start = to_ql_date(start or self.evaluation_date)
            ql_end = to_ql_date(end or self.maturity_date)

            if ql_start > ql_end:
                raise ValueError("Start date must be before end date")

            # Calculate the total period in years according to day count convention
            total_years = day_counter.yearFraction(ql_start, ql_end)

            # Calculate step size in years
            step_years = total_years / (points - 1)

            result = {}
            current = ql_start

            for i in range(points):
                if i == points - 1:  # Ensure we always include the end date
                    current = ql_end

                rate = curve.zeroRate(current, day_counter, compounding, frequency).rate()
                result[from_ql_date(current)] = rate

                # Advance using calendar and business day convention
                if i < points - 2:  # Don't advance after the second-to-last point
                    current = calendar.advance(
                        current,
                        Period(int(round(step_years * 365)), Days),
                        self.business_day_convention
                    )
                    current = min(current, ql_end)  # Don't go past end date

            return result

        except Exception as e:
            logging.error(f"Discount curve generation failed: {str(e)}", exc_info=True)
            return {}

    def summary(self) -> Dict[str, float]:
        if self._summary_cache is not None:
            return self._summary_cache

        metrics = {
            'clean_price': self.clean_price,
            'dirty_price': self.dirty_price,
            'accrued_interest': self.accrued_interest,
            'yield_to_maturity': self.yield_to_maturity,
            'yield_to_worst': self.yield_to_worst,
            'modified_duration': self.modified_duration,
            'macaulay_duration': self.macaulay_duration,
            'simple_duration': self.simple_duration,
            'convexity': self.convexity,
            'dv01': self.dv01,
            'normalized_price': self._get_normalized_market_price,
        }

        results = {}
        for name, method in metrics.items():
            try:
                results[name] = method()
            except Exception as e:
                results[name] = float('nan')
                logging.warning(f"Failed to calculate {name}: {str(e)}")

        try:
            results['cashflows'] = self.cashflows()
        except Exception as e:
            results['cashflows'] = []
            logging.warning(f"Failed to get cashflows: {str(e)}")

        summary_clean = replace_nan_with_none(results)

        self._summary_cache = summary_clean
        return summary_clean

    def invalidate_cache(self):
        self._summary_cache = None

    # Then, in methods that update key state, call invalidate_cache
    def update_yield_curve(self, rate: float) -> None:
        if not isinstance(rate, (float, int)) or rate < 0:
            raise ValueError("Rate must be a non-negative number")
        if self._rate_quote is None:
            self.build_quantlib_bond()
        self._rate_quote.setValue(rate)
        self.invalidate_cache()

    def update_evaluation_date(self, new_date: date) -> None:
        if to_ql_date(new_date) < self.issue_date:
            raise ValueError("Evaluation date cannot be before Issue date")
        if to_ql_date(new_date) > self.maturity_date:
            raise ValueError("Evaluation date cannot be after Maturity date")
        self.evaluation_date = to_ql_date(new_date)
        self._set_eval_date_and_settlement_date()
        self._bond = None
        self._discount_curve = None
        self._rate_quote = None
        self.invalidate_cache()
