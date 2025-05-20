import logging
import math
from datetime import date, date as pydate
from typing import Dict, List, Optional, Tuple

from QuantLib import (Annual, BondFunctions, Compounded, Date, Days, DiscountingBondEngine, Duration, FlatForward,
                      QuoteHandle, Settings, Simple, SimpleQuote, YieldTermStructureHandle, ZeroCouponBond)

from FixedIncome.analytics.BondAnalyticsFactory import BondAnalyticsBase
from FixedIncome.analytics.utils.helpers import replace_nan_with_none
from FixedIncome.analytics.utils.quantlib_helpers import from_ql_date, next_business_day, to_ql_date
from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel


class ZeroCouponBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: ZeroCouponBondModel):
        super().__init__(bond)
        self._summary_cache = None

        if not isinstance(bond, ZeroCouponBondModel):
            raise ValueError("Must provide a ZeroCouponBondModel instance")

        # Set evaluation date to today
        # TODO make it an input
        Settings.instance().evaluationDate = Date.todaysDate()

        self._bond: Optional[ZeroCouponBond] = None
        self._discount_curve: Optional[YieldTermStructureHandle] = None
        self._rate_quote: Optional[SimpleQuote] = None

        self._validate_inputs()
        self._adjust_settlement_date_for_holidays()

    def _adjust_settlement_date_for_holidays(self):
        original_settlement = to_ql_date(self.settlement_date)
        adjusted_settlement = next_business_day(original_settlement, self.calendar)

        if adjusted_settlement != original_settlement:
            logging.info(
                f"Settlement date adjusted from {from_ql_date(original_settlement)} to {from_ql_date(adjusted_settlement)} due to holiday.")

        self.settlement_date = adjusted_settlement

    def _adjust_maturity_date_for_holidays(self):
        original_maturity = to_ql_date(self.maturity_date)
        adjusted_maturity = next_business_day(original_maturity, self.calendar)

        if adjusted_maturity != original_maturity:
            logging.info(
                f"Maturity date adjusted from {from_ql_date(original_maturity)} to {from_ql_date(adjusted_maturity)} due to holiday.")

        self.maturity_date = adjusted_maturity

    def _validate_inputs(self):
        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date.")
        if self.face_value <= 0:
            raise ValueError("Face value must be positive.")
        if to_ql_date(self.settlement_date) < self.issue_date:
            raise ValueError("Settlement date cannot be before issue date.")

    def _build_yield_curve(self, initial_rate: float = 0.05) -> Tuple[YieldTermStructureHandle, SimpleQuote]:
        flat_rate = SimpleQuote(initial_rate)
        curve = FlatForward(
            self.settlement_date,
            QuoteHandle(flat_rate),
            self.day_count_convention,
            Compounded,
            Annual
        )
        return YieldTermStructureHandle(curve), flat_rate

    def build_quantlib_bond(self) -> ZeroCouponBond:
        if self._bond is None:

            self._bond = ZeroCouponBond(
                settlementDays=self.settlement_days,
                calendar=self.calendar,
                faceAmount=self.face_value,
                maturityDate=self.maturity_date,
                paymentConvention=self.convention,
                redemption=100.0,
                issueDate=self.issue_date
            )

            if self._discount_curve is None or self._rate_quote is None:
                self._discount_curve, self._rate_quote = self._build_yield_curve()

            self._bond.setPricingEngine(DiscountingBondEngine(self._discount_curve))

        return self._bond

    def cashflows(self) -> List[Tuple[pydate, float]]:
        try:
            bond = self.build_quantlib_bond()
            ql_settlement = to_ql_date(self.settlement_date)
            return [
                (cf.date(), cf.amount())
                for cf in bond.cashflows()
                if cf.date() >= ql_settlement and cf.amount() > 0
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
            market_price = getattr(self, 'market_price', None)
            if market_price is None:
                logging.warning("Market price not set, using clean price as fallback.")
                market_price = self.clean_price()

            return self.build_quantlib_bond().bondYield(
                market_price,
                self.day_count_convention,
                Compounded,
                Annual,
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
                Compounded,
                Annual,
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
                Compounded,
                Annual,
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
                Annual,
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
                Compounded,
                Annual,
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
            price_up = BondFunctions.cleanPrice(bond, ytm + bump_size, self.day_count_convention, Compounded, Annual,
                                                self.settlement_date)
            price_down = BondFunctions.cleanPrice(bond, ytm - bump_size, self.day_count_convention, Compounded, Annual,
                                                  self.settlement_date)

            return (price_down - price_up) / (2 * bump_size)
        except Exception as e:
            logging.error(f"DV01 calculation failed: {str(e)}")
            return float('nan')

    def get_discount_curve(self, start=None, end=None, frequency_days=365) -> Dict[str, float]:
        try:
            if self._discount_curve is None:
                self.build_quantlib_bond()

            curve = self._discount_curve.currentLink()
            calendar = self.calendar
            day_counter = self.day_count_convention

            start = to_ql_date(self.issue_date) or to_ql_date(start)
            end = to_ql_date(self.maturity_date) or to_ql_date(end)

            if start > end:
                raise ValueError("Start date must be before end date")

            result = {}
            current = start
            while current <= end:
                rate = curve.zeroRate(current, day_counter, Compounded, Annual).rate()
                result[current.isoformat()] = rate
                current = calendar.advance(current, frequency_days, Days)

            return result
        except Exception as e:
            logging.error(f"Discount curve generation failed: {str(e)}")
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
            'dv01': self.dv01
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

    def update_settlement_date(self, new_date: date) -> None:
        if new_date < self.issue_date:
            raise ValueError("Settlement cannot be before issue")
        self.settlement_date = new_date
        self._bond = None
        self._discount_curve = None
        self._rate_quote = None
        self.invalidate_cache()
