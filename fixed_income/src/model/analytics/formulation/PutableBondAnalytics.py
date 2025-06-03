import logging
import math
from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Tuple

from QuantLib import BondFunctions, BondPrice, Callability, CallabilitySchedule, CallableFixedRateBond, \
    DateGeneration, Days, Duration, FlatForward, HullWhite, Months, Period, QuoteHandle, Schedule, Settings, \
    Simple, SimpleQuote, \
    SobolRsg, TimeGrid, \
    TreeCallableFixedRateBondEngine, YieldTermStructureHandle

from fixed_income.src.model.analytics.formulation import BondAnalyticsBase
from fixed_income.src.model.bonds import PutableBondModel
from fixed_income.src.utils.helpers import replace_nan_with_none
from fixed_income.src.utils.quantlib_mapper import from_ql_date, to_ql_date, to_ql_frequency


class PutableBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: PutableBondModel):
        super().__init__(bond)

        if not isinstance(bond, PutableBondModel):
            raise ValueError("Must provide a PutableBondModel instance")

        self._summary_cache = None

        self._bond: Optional[CallableFixedRateBond] = None
        self._discount_curve: Optional[YieldTermStructureHandle] = None
        self._rate_quote: Optional[SimpleQuote] = None

        self.coupon_rate = bond.coupon_rate
        self.coupon_frequency = to_ql_frequency(bond.coupon_frequency)
        self.schedule = None

        self.put_schedule = bond.put_schedule
        self.putability_schedule = CallabilitySchedule()

        # Adjust dates to business days
        self._adjust_dates()

        # Global declaration to anchor the calculation point(valuation_date/as_of_date)
        self._set_eval_date_and_settlement_date()
        self._validate_inputs()

    def _adjust_dates(self) -> None:
        """Adjust all relevant dates according to calendar and business day convention."""
        self.issue_date = self.calendar.adjust(self.issue_date, self.business_day_convention)
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

        if not 0 <= self.coupon_rate <= 1:
            raise ValueError("Coupon rate must be between 0 and 1 (0% to 100%)")

        if hasattr(self, 'market_price') and self.market_price is not None:
            if self.market_price <= 0:
                raise ValueError("Market price must be positive")
        if self.put_schedule is None:
            raise ValueError("Put schedule required for Putable bond")

    def _set_eval_date_and_settlement_date(self):
        Settings.instance().evaluationDate = self.evaluation_date
        if self.settlement_days == 0:
            self.settlement_date = self.evaluation_date  # Avoid unnecessary advance
        else:
            self.settlement_date = self.calendar.advance(
                self.evaluation_date,
                self.settlement_days,
                Days
            )
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

    def _build_coupon_schedule(self):
        return Schedule(
            self.issue_date,
            self.maturity_date,
            Period(int(12 / self.coupon_frequency), Months),
            self.calendar,
            self.business_day_convention,
            self.business_day_convention,
            DateGeneration.Backward,
            False
        )

    def _filter_put_schedule(self) -> List[Dict]:
        """Filter out historical put dates and validate remaining schedule."""
        if not self.put_schedule:
            return []

        filtered_schedule = []
        for entry in self.put_schedule:
            if not isinstance(entry, dict) or "date" not in entry or "price" not in entry:
                raise ValueError("Put schedule entries must be dicts with 'date' and 'price' keys")

            put_date = to_ql_date(date.fromisoformat(entry["date"]))
            adjusted_put_date = self.calendar.adjust(put_date, self.business_day_convention)

            # Only include put dates that are in the future relative to evaluation date
            if adjusted_put_date > self.evaluation_date:
                filtered_schedule.append({
                    "date": adjusted_put_date,
                    "price": float(entry["price"])
                })

        # Sort the call schedule by date
        filtered_schedule.sort(key=lambda x: x["date"])
        return filtered_schedule

    def _build_putability_schedule(self):
        """Build callability schedule considering only future put dates."""
        filtered_schedule = self._filter_put_schedule()

        if not filtered_schedule:
            logging.warning("No valid future put dates found in put schedule")
            return

        for entry in self.put_schedule:
            if not isinstance(entry, dict) or "date" not in entry or "price" not in entry:
                raise ValueError("Put schedule entries must be dicts with 'date' and 'price' keys")

            schedule_date = self.calendar.adjust(
                to_ql_date(date.fromisoformat(entry["date"])),
                self.business_day_convention
            )

            schedule_price = float(entry["price"])
            if schedule_price <= 0:
                raise ValueError("Put price must be positive")

            self.putability_schedule.append(Callability(
                BondPrice(schedule_price, BondPrice.Dirty),
                Callability.Call,
                schedule_date
            ))

    def build_quantlib_bond(self,
                            mean_reversion: float = 0.05,
                            volatility: float = 0.01,
                            time_steps: int = 100) -> CallableFixedRateBond:
        """Lazily construct and return the QuantLib PutableFixedRateBond object"""
        if self.schedule is None:
            self.schedule = self._build_coupon_schedule()

        if self.put_schedule is None:
            self._build_putability_schedule()

        if self._bond is None:
            self._bond = CallableFixedRateBond(
                settlementDays=self.settlement_days,
                faceAmount=self.face_value,
                schedule=self.schedule,
                coupons=[self.coupon_rate],
                accrualDayCounter=self.day_count_convention,
                paymentConvention=self.business_day_convention,
                redemption=100.0,
                issueDate=self.issue_date,
                putCallSchedule=self.putability_schedule,
            )

            if self._discount_curve is None or self._rate_quote is None:
                self._discount_curve, self._rate_quote = self._build_yield_curve()

            # Set pricing engine with the properly constructed discount curve
            model = HullWhite(self._discount_curve)

            years_to_maturity = self._discount_curve.referenceDate().yearFraction(self.maturity_date)
            time_grid = TimeGrid(years_to_maturity, 100)

            engine = TreeCallableFixedRateBondEngine(model, time_grid)
            self._bond.setPricingEngine(engine)

        return self._bond

    def cashflows(self) -> List[Tuple[date, float]]:
        try:
            bond = self.build_quantlib_bond()

            cashflows_by_date = defaultdict(float)

            for cf in bond.cashflows():
                if not cf.hasOccurred():
                    cf_date = from_ql_date(cf.date())
                    cf_amount = cf.amount()
                    if not isinstance(cf_amount, (float, int)):
                        raise ValueError(f"Invalid cashflow amount {cf_amount} for date {cf_date}")
                    # optionally skip past cashflows
                    cashflows_by_date[from_ql_date(cf.date())] += cf.amount()

            # Return as sorted list of (Date, Amount) tuples
            return sorted(cashflows_by_date.items(), key=lambda x: x[0])
        except Exception as e:
            logging.error(f"Failed to get cashflows: {str(e)}")
            return []

    def clean_price(self) -> float:
        """Returns clean price normalized to face value of 1000"""
        try:
            ql_price = self.build_quantlib_bond().cleanPrice()  # QL returns price per 100
            return ql_price * (self.face_value / 100.0)
        except Exception as e:
            logging.error(f"Clean price calculation failed: {str(e)}")
            return float('nan')

    def dirty_price(self) -> float:
        """Returns dirty price normalized to face value of 1000"""
        try:
            ql_price = self.build_quantlib_bond().dirtyPrice()  # QL returns price per 100
            return ql_price * (self.face_value / 100.0)
        except Exception as e:
            logging.error(f"Dirty price calculation failed: {str(e)}")
            return float('nan')

    def accrued_interest(self) -> float:
        """Returns accrued interest normalized to face value of 1000"""
        try:
            ql_accrued = self.build_quantlib_bond().accruedAmount()  # QL returns per 100
            return ql_accrued * (self.face_value / 100.0)
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

    def yield_to_put(self) -> float:
        """
        Returns the Yield to Put (YTP), calculated to the earliest put date after settlement.
        If no future put date is available, returns NaN.
        """
        try:
            bond = self.build_quantlib_bond()

            # Find the first put date strictly after settlement
            future_puts = [c for c in self.putability_schedule if c.date() > self.evaluation_date]
            if not future_puts:
                logging.warning("No future put dates available to compute YTP.")
                return float('nan')

            first_put = min(future_puts, key=lambda c: c.date())
            put_date = first_put.date()
            put_price = first_put.price().amount()

            return BondFunctions.bondYield(
                bond,
                put_price,
                self.day_count_convention,
                self.compounding,
                self.frequency,
                self.settlement_date,
                put_date
            )

        except Exception as e:
            logging.error(f"YTP calculation failed: {str(e)}")
            return float('nan')

    def yield_to_worst(self) -> float:
        """
        Returns Yield to Worst (YTW).
        """
        return min(self.yield_to_maturity(), self.yield_to_put())

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

    def calculate_key_rate_durations(self, key_rates: List[float], bump_size: float = 0.0001) -> Dict[float, float]:
        """
        Calculate key rate durations (partial durations) for specified rate points.

        Args:
            key_rates: List of key rate points in years (e.g., [1, 2, 5, 10, 30])
            bump_size: Size of rate shock (in decimal, e.g., 0.0001 for 1bp)

        Returns:
            Dictionary mapping key rate points to their respective durations
        """
        try:
            if not key_rates:
                raise ValueError("Key rates list cannot be empty")

            if bump_size <= 0:
                raise ValueError("Bump size must be positive")

            # Sort and validate key rates
            key_rates = sorted(float(rate) for rate in key_rates)
            if any(rate <= 0 for rate in key_rates):
                raise ValueError("All key rates must be positive")

            # Get base price
            base_price = self.clean_price()

            # Initialize results
            krd_results = {}

            # Store original curve
            original_rate = self._rate_quote.value()

            # Calculate for each key rate
            for rate_point in key_rates:
                # Create shocked curves
                up_curve = self._create_parallel_shocked_curve(rate_point, bump_size)
                down_curve = self._create_parallel_shocked_curve(rate_point, -bump_size)

                # Price under shocked curves
                price_up = self._price_with_shocked_curve(up_curve)
                price_down = self._price_with_shocked_curve(down_curve)

                # Calculate KRD
                krd = (price_down - price_up) / (2 * bump_size * base_price)
                krd_results[rate_point] = krd

            # Restore original curve
            self._rate_quote.setValue(original_rate)
            self.invalidate_cache()

            return krd_results

        except Exception as e:
            logging.error(f"Key rate duration calculation failed: {str(e)}", exc_info=True)
            return {rate: float('nan') for rate in key_rates}

    def _create_parallel_shocked_curve(self, rate_point: float, shock_size: float):
        """Create a shocked curve at specific rate point"""
        # Clone the original curve
        original_curve = self._discount_curve.currentLink()

        # Create new quotes for each shock scenario
        shocked_quote = SimpleQuote(original_curve.zeroRate(
            rate_point,
            self.day_count_convention,
            self.compounding,
            self.frequency
        ).rate() + shock_size)

        return FlatForward(
            self.evaluation_date,
            QuoteHandle(shocked_quote),
            self.day_count_convention,
            self.compounding,
            self.frequency
        )

    def _price_with_shocked_curve(self, shocked_curve):
        """Calculate bond price with temporary shocked curve"""
        # Store original engine
        original_engine = self._bond.pricingEngine()

        try:
            # Create temporary pricing engine with shocked curve
            model = HullWhite(YieldTermStructureHandle(shocked_curve))
            time_grid = TimeGrid(
                shocked_curve.referenceDate().yearFraction(self.maturity_date),
                self.model_params["time_steps"]
            )
            temp_engine = TreeCallableFixedRateBondEngine(model, time_grid)

            # Price with shocked curve
            self._bond.setPricingEngine(temp_engine)
            return self._bond.cleanPrice()
        finally:
            # Restore original engine
            self._bond.setPricingEngine(original_engine)

    def call_probability(self, num_paths: int = 1000) -> Dict[date, float]:
        """
        Estimate probability of bond being called at each call date using Monte Carlo simulation.

        Args:
            num_paths: Number of Monte Carlo paths to simulate

        Returns:
            Dictionary mapping call dates to their respective call probabilities
        """
        try:
            if not self.putability_schedule:
                return {}

            # Get future call dates
            future_calls = [
                (c.date(), c.price().amount())
                for c in self.putability_schedule
                if c.date() > self.evaluation_date
            ]

            if not future_calls:
                return {}

            # Sort call dates
            future_calls.sort(key=lambda x: x[0])

            # Set up Hull-White model
            model = HullWhite(
                self._discount_curve,
                self.model_params["mean_reversion"],
                self.model_params["volatility"]
            )

            # Create sequence generator
            seed = 42  # For reproducibility
            sequence_generator = SobolRsg(1)  # 1-dimensional

            # Simulate paths
            call_counts = defaultdict(int)

            for _ in range(num_paths):
                # Generate random path
                path = self._generate_interest_rate_path(
                    model,
                    max(c[0] for c in future_calls),
                    sequence_generator
                )

                # Check each call date
                for call_date, call_price in future_calls:
                    # Get simulated short rate at call date
                    rate = path[call_date]

                    # Create temporary curve
                    temp_curve = FlatForward(
                        call_date,
                        QuoteHandle(SimpleQuote(rate)),
                        self.day_count_convention,
                        self.compounding,
                        self.frequency
                    )

                    # Price bond if not called yet
                    bond_value = self._calculate_bond_value_at_date(call_date, temp_curve)

                    # Check if called
                    if bond_value >= call_price:
                        call_counts[from_ql_date(call_date)] += 1
                        break  # Bond is called, no later calls matter

            # Calculate probabilities
            total_paths = float(num_paths)
            probabilities = {
                call_date: count / total_paths
                for call_date, count in call_counts.items()
            }

            # Add zero probabilities for dates that were never called
            for call_date, _ in future_calls:
                ql_date = to_ql_date(call_date)
                if ql_date not in probabilities:
                    probabilities[ql_date] = 0.0

            return probabilities

        except Exception as e:
            logging.error(f"Call probability calculation failed: {str(e)}", exc_info=True)
            return {}

    def _generate_interest_rate_path(self, model, end_date, sequence_generator):
        """Generate a single interest rate path using the model"""
        # Convert dates to times
        times = [self.day_count_convention.yearFraction(
            self.evaluation_date,
            date
        ) for date in [self.evaluation_date, end_date]]

        # Generate random numbers
        sequence = sequence_generator.nextSequence().value()

        # Simulate path
        path = {}
        time_grid = TimeGrid(times[0], times[1], 100)
        process = model.treeProcess(time_grid)

        # Store the path at each call date
        for call_date in self.putability_schedule:
            ql_date = call_date.date()
            if ql_date > self.evaluation_date:
                t = self.day_count_convention.yearFraction(self.evaluation_date, ql_date)
                path[ql_date] = process.evolve(0, 0, t, sequence[0])

        return path

    def _calculate_bond_value_at_date(self, call_date, temp_curve):
        """Calculate bond value at a specific future date"""
        # Temporarily change evaluation date
        Settings.instance().evaluationDate = call_date

        try:
            # Create temporary bond
            temp_bond = CallableFixedRateBond(
                settlementDays=0,  # Immediate settlement
                faceAmount=self.face_value,
                schedule=self.schedule,
                coupons=[self.coupon_rate],
                paymentDayCounter=self.day_count_convention,
                paymentConvention=self.business_day_convention,
                redemption=100.0,
                issueDate=self.issue_date,
                putCallSchedule=self.putability_schedule,
                paymentCalendar=self.calendar
            )

            # Set pricing engine
            temp_model = HullWhite(YieldTermStructureHandle(temp_curve))
            time_grid = TimeGrid(
                temp_curve.referenceDate().yearFraction(self.maturity_date),
                self.model_params["time_steps"]
            )
            temp_engine = TreeCallableFixedRateBondEngine(temp_model, time_grid)
            temp_bond.setPricingEngine(temp_engine)

            return temp_bond.cleanPrice()
        finally:
            # Restore original evaluation date
            Settings.instance().evaluationDate = self.evaluation_date

    def summary(self) -> Dict[str, float]:
        """Returns a dictionary of all key bond analytics with safe evaluation"""
        metrics = {
            'clean_price': self.clean_price,
            'dirty_price': self.dirty_price,
            'accrued_interest': self.accrued_interest,
            'yield_to_maturity': self.yield_to_maturity,
            'yield_to_put': self.yield_to_put,
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
