import logging
import math
from datetime import date
from typing import Dict, List, Tuple

from QuantLib import Annual, BondFunctions, BondPrice, Callability, CallabilitySchedule, CallableFixedRateBond, \
    Compounded, DateGeneration, Days, Duration, FlatForward, HullWhite, Months, Period, QuoteHandle, Schedule, Settings, \
    Simple, SimpleQuote, TimeGrid, \
    TreeCallableFixedRateBondEngine, YieldTermStructureHandle

from FixedIncome.analytics.formulation.BondAnalyticsBase import BondAnalyticsBase
from FixedIncome.analytics.utils.quantlib_mapper import to_ql_date
from FixedIncome.model.CallableBondModel import CallableBondModel


class CallableBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: CallableBondModel):
        super().__init__(bond)

        if not isinstance(bond, CallableBondModel):
            raise ValueError("Must provide a CallableBondModel instance")

        # Adjust settlement date if it's a holiday
        self._adjust_settlement_date_for_holidays()

        # Set QuantLib evaluation date to settlement date - #impotant
        Settings.instance().evaluationDate = self.settlement_date

        self._bond = None
        self._discount_curve = None
        self._rate_quote = None
        self._validate_inputs()

        self.coupon_rate = bond.coupon_rate
        self.coupon_frequency = bond.coupon_frequency
        self.schedule = None

        self.call_schedule = bond.call_schedule
        self.callability_schedule = CallabilitySchedule()

    def _adjust_settlement_date_for_holidays(self):
        """
        Adjust the settlement date if it falls on a holiday.
        Moves to the next business day if necessary.
        """
        original_date = self.settlement_date
        while not self.calendar.isBusinessDay(self.settlement_date):
            self.settlement_date = self.calendar.advance(
                self.settlement_date,
                1,
                Days
            )
        logging.info(f"Adjusted settlement date from {original_date} to {self.settlement_date} due to holiday")

    def _validate_inputs(self):
        """Validate bond parameters before QuantLib object creation"""
        if self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date")
        if self.face_value <= 0:
            raise ValueError("Face value must be positive")
        if self.settlement_date < self.issue_date:
            raise ValueError("Settlement date cannot be before issue date")

    def _build_yield_curve(self, initial_rate: float = 0.05) -> Tuple[YieldTermStructureHandle, SimpleQuote]:
        """Separate yield curve construction for better maintainability"""
        flat_rate = SimpleQuote(initial_rate)

        # Use settlement date as reference date for the curve
        curve = FlatForward(
            self.settlement_date,
            QuoteHandle(flat_rate),
            self.day_count_convention,
            Compounded,
            Annual
        )

        return YieldTermStructureHandle(curve), flat_rate

    def _build_coupon_schedule(self):
        return Schedule(
            self.issue_date,
            self.maturity_date,
            Period(int(12 / self.coupon_frequency.value), Months),
            self.calendar,
            self.convention,
            self.convention,
            DateGeneration.Backward,
            False
        )

    def _build_callability_schedule(self):
        for entry in self.call_schedule:
            schedule_date = to_ql_date(date.fromisoformat(entry["date"]))
            schedule_price = entry["price"]
            self.callability_schedule.append(Callability(
                BondPrice(schedule_price, BondPrice.Clean),
                Callability.Call,
                schedule_date
            ))

    def build_quantlib_bond(self) -> CallableFixedRateBond:
        """Lazily construct and return the QuantLib CallableFixedRateBond object"""
        if self.schedule is None:
            self.schedule = self._build_coupon_schedule()

        if self.call_schedule and len(self.callability_schedule) == 0:
            self._build_callability_schedule()

        if self._bond is None:
            # Create bond instrument
            self._bond = CallableFixedRateBond(
                settlementDays=1,
                faceAmount=self.face_value,
                schedule=self.schedule,
                coupons=[self.coupon_rate],
                dayCounter=self.day_count_convention,
                paymentConvention=self.convention,
                redemption=100.0,
                issueDate=self.issue_date,
                putCallSchedule=self.callability_schedule
            )

            # Build and attach yield curve
            self._discount_curve, self._rate_quote = self._build_yield_curve()

            # Set pricing engine with the properly constructed discount curve
            model = HullWhite(self._discount_curve)

            years_to_maturity = self._discount_curve.referenceDate().yearFraction(self.maturity_date)
            time_grid = TimeGrid(years_to_maturity, 100)

            engine = TreeCallableFixedRateBondEngine(model, time_grid)
            self._bond.setPricingEngine(engine)

        return self._bond

    def cashflows(self) -> List[Tuple[date, float]]:
        """Returns all future cashflows as (date, amount) tuples"""
        bond = self.build_quantlib_bond()
        return [(cf.date(), cf.amount()) for cf in bond.cashflows() if
                cf.date() >= self.settlement_date and cf.amount() > 0]

    def clean_price(self) -> float:
        """Returns the clean price using QuantLib's pricing engine"""
        try:
            # Ensure QuantLib evaluation date is current
            Settings.instance().evaluationDate = self.settlement_date

            bond = self.build_quantlib_bond()

            return bond.cleanPrice()

        except Exception as e:
            logging.error(f"Clean price calculation failed: {str(e)}")
            return float('nan')

    def dirty_price(self) -> float:
        """Returns the dirty price using QuantLib's built-in method"""
        try:
            # Ensure QuantLib evaluation date is current
            Settings.instance().evaluationDate = self.settlement_date

            bond = self.build_quantlib_bond()

            return bond.dirtyPrice()

        except Exception as e:
            logging.error(f"Dirty price calculation failed: {str(e)}")
            return float('nan')

    def accrued_interest(self) -> float:
        """Returns the accrued interest since last cashflow"""
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date
            return self.build_quantlib_bond().accruedAmount()
        except Exception as e:
            logging.error(f"Accrued interest calculation failed: {str(e)}")
            return float('nan')

    def yield_to_maturity(self) -> float:
        """
        Returns the Yield to Maturity (YTM) given the market price.
        Computed with Compounded Annual convention.
        """
        try:
            if self.market_price is None:
                raise ValueError("Market price must be set before calculating yield to maturity")

            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

            return self.build_quantlib_bond().bondYield(
                self.market_price,
                self.day_count_convention,
                Compounded,
                Annual,
                self.settlement_date
            )
        except Exception as e:
            logging.error(f"YTM calculation failed: {str(e)}")
            return float('nan')

    def yield_to_call(self) -> float:
        """
        Returns the Yield to Call (YTC), calculated to the earliest call date after settlement.
        If no future call date is available, returns NaN.
        """
        try:
            Settings.instance().evaluationDate = self.settlement_date
            bond = self.build_quantlib_bond()

            # Find the first call date strictly after settlement
            future_calls = [c for c in self.callability_schedule if c.date() > self.settlement_date]
            if not future_calls:
                logging.warning("No future call dates available to compute YTC.")
                return float('nan')

            first_call = min(future_calls, key=lambda c: c.date())
            call_date = first_call.date()
            call_price = first_call.price().amount()

            return BondFunctions.bondYield(
                bond,
                call_price,
                self.day_count_convention,
                Compounded,
                Annual,
                self.settlement_date,
                call_date
            )

        except Exception as e:
            logging.error(f"YTC calculation failed: {str(e)}")
            return float('nan')

    def yield_to_worst(self) -> float:
        """
        Returns Yield to Worst (YTW).
        """
        return min(self.yield_to_maturity(), self.yield_to_call())

    def modified_duration(self) -> float:
        """Returns the modified duration in years"""
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

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
        """Returns the Macaulay duration in years"""
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

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
        """Returns simple duration approximation"""
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

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
        """Returns convexity measure"""
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

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
        """
        Returns DV01 (Dollar Value of 1 basis point)

        Args:
            bump_size: The yield change to use (default 1bp)
        """
        try:
            # Ensure evaluation date is set correctly
            Settings.instance().evaluationDate = self.settlement_date

            ytm = self.yield_to_maturity()
            if math.isnan(ytm):
                return float('nan')

            bond = self.build_quantlib_bond()

            price_up = BondFunctions.cleanPrice(
                bond,
                ytm + bump_size,
                self.day_count_convention,
                Compounded,
                Annual,
                self.settlement_date
            )

            price_down = BondFunctions.cleanPrice(
                bond,
                ytm - bump_size,
                self.day_count_convention,
                Compounded,
                Annual,
                self.settlement_date
            )

            return (price_down - price_up) / 2
        except Exception as e:
            logging.error(f"DV01 calculation failed: {str(e)}")
            return float('nan')

    def get_discount_curve(self, start=None, end=None, frequency_days=365) -> Dict[str, float]:
        """
        Returns a dictionary of {ISO_date: zero_rate} over the selected range.

        Args:
            start: Start date (defaults to issue date)
            end: End date (defaults to maturity date)
            frequency_days: Sampling frequency in days
        """
        try:
            if self._discount_curve is None:
                self.build_quantlib_bond()

            curve = self._discount_curve.currentLink()
            calendar = self.calendar
            day_counter = self.day_count_convention

            start = start or self.issue_date
            end = end or self.maturity_date

            if start > end:
                raise ValueError("Start date must be before end date")

            result = {}
            current = start

            while current <= end:
                rate = curve.zeroRate(
                    current,
                    day_counter,
                    Compounded,
                    Annual
                ).rate()
                result[current.ISO()] = rate
                current = calendar.advance(current, frequency_days, Days)

            return result
        except Exception as e:
            logging.error(f"Discount curve generation failed: {str(e)}")
            return {}

    def summary(self) -> Dict[str, float]:
        """Returns a dictionary of all key bond analytics with safe evaluation"""
        metrics = {
            'clean_price': self.clean_price,
            'dirty_price': self.dirty_price,
            'accrued_interest': self.accrued_interest,
            'yield_to_maturity': self.yield_to_maturity,
            'yield_to_call': self.yield_to_call,
            'yield_to_worst': self.yield_to_worst,
            'modified_duration': self.modified_duration,
            'macaulay_duration': self.macaulay_duration,
            'simple_duration': self.simple_duration,
            'convexity': self.convexity,
            'dv01': lambda: self.dv01(0.0001)
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

        return results

    def update_yield_curve(self, rate: float) -> None:
        """Update the yield curve with a new rate"""
        if not isinstance(rate, (float, int)) or rate < 0:
            raise ValueError("Rate must be a non-negative number")

        if self._rate_quote is None:
            self.build_quantlib_bond()

        self._rate_quote.setValue(rate)

    def update_settlement_date(self, new_date: date) -> None:
        """
        Update settlement date and QuantLib evaluation date
        """
        if new_date < self.issue_date:
            raise ValueError("Settlement cannot be before issue")

        # Update QuantLib global evaluation date
        self.settlement_date = new_date
        Settings.instance().evaluationDate = self.settlement_date

        # Force rebuild of bond and curve
        self._bond = None
        self._discount_curve = None
        self._rate_quote = None
