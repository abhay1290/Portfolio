import logging
import math
from collections import defaultdict
from datetime import date, datetime
from typing import DefaultDict, Dict, List, Optional, Tuple

from QuantLib import (AmortizingFixedRateBond, BondFunctions, Date, DateGeneration, Days,
                      DiscountingBondEngine, Duration, FlatForward, Months, Period, QuoteHandle, Schedule,
                      Settings,
                      Simple, SimpleQuote, YieldTermStructureHandle)

from FixedIncome.analytics.formulation.BondAnalyticsBase import BondAnalyticsBase
from FixedIncome.analytics.utils.helpers import replace_nan_with_none
from FixedIncome.analytics.utils.quantlib_mapper import from_ql_date, to_ql_date, to_ql_frequency
from FixedIncome.model.SinkingFundBondModel import SinkingFundBondModel


class SinkingFundBondAnalytics(BondAnalyticsBase):
    def __init__(self, bond: SinkingFundBondModel):
        super().__init__(bond)

        if not isinstance(bond, SinkingFundBondModel):
            raise ValueError("Must provide a SinkingFundBondModel instance")

        self._summary_cache = None

        self._bond: Optional[AmortizingFixedRateBond] = None
        self._discount_curve: Optional[YieldTermStructureHandle] = None
        self._rate_quote: Optional[SimpleQuote] = None

        self.coupon_rate = bond.coupon_rate
        self.coupon_frequency = to_ql_frequency(bond.coupon_frequency)
        self.schedule = None

        self.sinking_schedule = bond.sinking_fund_schedule
        # TODO add treatment based on type
        self.sinking_fund_type = bond.sinking_fund_type

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

    def _validate_callability_schedule(self):
        """Validate sinking fund schedule specifics."""
        total_sinking = sum(x['notional'] for x in self.sinking_schedule)

        if abs(total_sinking - self.face_value) > 1e-6:  # Floating point tolerance
            raise ValueError(
                f"Total sinking payments ({total_sinking}) "
                f"must equal face value ({self.face_value})"
            )

        # Check for duplicate dates
        dates = [x['date'] for x in self.sinking_schedule]
        if len(dates) != len(set(dates)):
            raise ValueError("Duplicate dates in sinking schedule")

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

    def _build_notionals_schedule(self) -> DefaultDict[Date, float]:
        if self.sinking_schedule is None:
            raise ValueError("Sinking fund schedule is missing.")

        # Sort schedule by date (optional, ensures chronological order)
        schedule = sorted(self.sinking_schedule, key=lambda x: x['date'])

        sinking_fund_by_date = defaultdict(float)

        for entry in schedule:
            try:
                iso_date = entry['date']
                notional = entry['notional']
                ql_date = Date.from_date(datetime.strptime(iso_date, "%Y-%m-%d").date())
            except Exception as e:
                raise ValueError(f"Invalid notional schedule entry: {entry} | Error: {e}")

            sinking_fund_by_date[ql_date] += float(notional)

        return sinking_fund_by_date

    def _validate_and_align_notionals_with_schedule(self) -> list[float]:

        schedule_dates = [self.schedule.date(i) for i in range(1, self.schedule.size())]
        if len(self.sinking_schedule) != len(schedule_dates):
            raise ValueError(
                f"Mismatch between notional schedule ({len(self.sinking_schedule)}) "
                f"and bond schedule periods ({len(schedule_dates)})."
            )

        for i, (notional_date, schedule_date) in enumerate(zip(self.sinking_schedule.keys(), schedule_dates)):
            if notional_date != schedule_date:
                raise ValueError(
                    f"Sinking fund date at index {i} ({notional_date}) does not match "
                    f"schedule date ({schedule_date})."
                )

        return self.sinking_schedule.values()

    def build_quantlib_bond(self) -> AmortizingFixedRateBond:
        if self.schedule is None:
            self.schedule = self._build_coupon_schedule()

        if self.sinking_schedule is None:
            self.sinking_schedule = self._build_notionals_schedule()

        if self._bond is None:
            self._bond = AmortizingFixedRateBond(
                settlementDays=self.settlement_days,
                notionals=self._validate_and_align_notionals_with_schedule(),
                schedule=self.schedule,
                coupons=[self.coupon_rate],
                accrualDayCounter=self.day_count_convention,
                paymentConvention=self.business_day_convention,
                redemption=100.0,
                issueDate=self.issue_date,
                paymentCalendar=self.calendar
            )

            if self._discount_curve is None or self._rate_quote is None:
                self._discount_curve, self._rate_quote = self._build_yield_curve()

            engine = DiscountingBondEngine(self._discount_curve)
            self._bond.setPricingEngine(engine)

        return self._bond

    # def build_bond_with_callability_schedule(self) -> Bond:
    #     """Build a bond with exact sinking fund dates using CallabilitySchedule."""
    #     # Create regular coupon schedule
    #     schedule = self._build_coupon_schedule()
    #
    #     # Convert sinking schedule to CallabilitySchedule
    #     callability_schedule = CallabilitySchedule()
    #     for entry in self.sinking_schedule:
    #         amount = entry['notional']
    #         call_date = Date.from_date(datetime.strptime(entry['date'], "%Y-%m-%d").date())
    #
    #         # Create callability price object (100 = percentage of face value)
    #         price = Callability.Price(amount / self.face_value * 100,
    #                                   Callability.Price.Clean)
    #
    #         # Create callability object (Put = sinking fund payment)
    #         callability = Callability(price,
    #                                   Callability.Put,
    #                                   call_date)
    #         callability_schedule.append(callability)
    #
    #     # Build the bond
    #     bond = Bond(
    #         self.settlement_days,
    #         self.calendar,
    #         self.issue_date,
    #         callability_schedule
    #     )
    #
    #     # Add coupon schedule
    #     bond.setupArguments(
    #         schedule=schedule,
    #         coupons=[self.coupon_rate],
    #         dayCounter=self.day_count_convention
    #     )
    #
    #     # Set pricing engine
    #     if self._discount_curve is None:
    #         self._discount_curve, self._rate_quote = self._build_yield_curve()
    #     bond.setPricingEngine(DiscountingBondEngine(self._discount_curve))
    #
    #     return bond

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

    # def cashflows(self) -> List[Tuple[date, float]]:
    #     bond = self.build_bond_with_callability_schedule()
    #     cashflows = []
    #
    #     for cf in bond.cashflows():
    #         cf_date = from_ql_date(cf.date())
    #         amount = cf.amount()
    #
    #         # Identify sinking payments
    #         if hasattr(cf, 'callability'):
    #             cashflows.append((cf_date, -amount))  # Negative for principal outflows
    #         else:
    #             cashflows.append((cf_date, amount))  # Positive for coupon inflows
    #
    #     return sorted(cashflows, key=lambda x: x[0])

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

    def yield_to_worst(self) -> float:
        """
        Returns Yield to Worst (YTW).
        For non-callable zero-coupon bonds, YTW = YTM.
        """
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
