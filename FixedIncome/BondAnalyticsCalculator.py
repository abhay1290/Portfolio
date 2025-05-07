from datetime import date

from QuantLib import *

from FixedIncome.CouponFrequencyEnum import CouponFrequencyEnum


def _convert_frequency(freq_enum: CouponFrequencyEnum):
    """Map custom CouponFrequencyEnum to QuantLib Frequency"""
    frequency_map = {
        CouponFrequencyEnum.ANNUAL: Annual,
        CouponFrequencyEnum.SEMI_ANNUAL: Semiannual,
        CouponFrequencyEnum.QUARTERLY: Quarterly,
    }
    return frequency_map.get(freq_enum)


class BondAnalyticsCalculator:
    def __init__(self, bond_analytics):
        self.bond = bond_analytics.bond
        self.settlement_date = bond_analytics.settlement_date
        self.day_counter = bond_analytics.day_count_convention
        self.frequency = _convert_frequency(bond_analytics.frequency)
        self.market_price = bond_analytics.market_price
        self.discount_curve = bond_analytics.disc
        self.call_schedule = getattr(bond_analytics, "call_schedule", None)
        self.put_schedule = getattr(bond_analytics, "put_schedule", None)

    def calculate(self) -> dict:
        try:
            # Yield to maturity (YTM) calculation
            ytm = BondFunctions.bondYield(
                self.bond,
                self.market_price,
                self.day_counter,
                Compounded,
                self.frequency,
                self.settlement_date
            )
        except RuntimeError as e:
            print(f"YTM calculation failed: {e}")
            ytm = None  # Or fallback to 0 or raise

        # Price calculations
        clean_price = BondFunctions.cleanPrice(
            self.bond,
            self.discount_curve
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )

        dirty_price = BondFunctions.dirtyPrice(
            self.bond,
            ytm,
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )

        accrued_interest = BondFunctions.accruedAmount(
            self.bond,
            self.settlement_date
        )

        # Duration calculations
        mod_duration = BondFunctions.duration(
            self.bond,
            ytm,
            self.day_counter,
            Compounded,
            self.frequency,
            Duration.Modified,
            self.settlement_date
        )

        mac_duration = BondFunctions.duration(
            self.bond,
            ytm,
            self.day_counter,
            Compounded,
            self.frequency,
            Duration.Macaulay,
            self.settlement_date
        )

        # Convexity calculation
        convexity = BondFunctions.convexity(
            self.bond,
            ytm,
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )

        # Risk measures
        dv01 = self._dv01_perturbation(ytm)
        ytw = self._yield_to_worst()

        return {
            "clean_price": clean_price,
            "dirty_price": dirty_price,
            "accrued_interest": accrued_interest,
            "yield_to_maturity": ytm,
            "yield_to_worst": ytw,
            "modified_duration": mod_duration,
            "macaulay_duration": mac_duration,
            "convexity": convexity,
            "dv01": dv01,
            "cashflows": self.cashflows()
        }

    def _dv01_perturbation(self, ytm: float) -> float:
        """Calculate DV01 using parallel yield curve shifts"""
        up = BondFunctions.cleanPrice(
            self.bond,
            ytm + 0.0001,
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )

        down = BondFunctions.cleanPrice(
            self.bond,
            ytm - 0.0001,
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )

        return (down - up) / 2  # DV01 per 1bp

    def _yield_to_worst(self) -> float:
        """Calculate yield to worst considering call/put features"""
        ytw_candidates = [BondFunctions.bondYield(
            self.bond,
            self.market_price,
            self.day_counter,
            Compounded,
            self.frequency,
            self.settlement_date
        )]

        # Add maturity yield

        # Process call schedule
        if self.call_schedule:
            for call in self.call_schedule:
                ytw_candidates.append(
                    BondFunctions.yieldToCall(
                        self.bond,
                        self.market_price,
                        _to_ql_date(call['date']),
                        call['price'],
                        self.day_counter,
                        Compounded,
                        self.frequency,
                        self.settlement_date
                    )
                )

        # Process put schedule
        if self.put_schedule:
            for put in self.put_schedule:
                ytw_candidates.append(
                    BondFunctions.yieldToPut(
                        self.bond,
                        self.market_price,
                        _to_ql_date(put['date']),
                        put['price'],
                        self.day_counter,
                        Compounded,
                        self.frequency,
                        self.settlement_date
                    )
                )

        return min(ytw_candidates) if ytw_candidates else None

    def cashflows(self):
        """Get future cashflows"""
        return [
            (cf.date().ISO(), cf.amount())
            for cf in self.bond.cashflows()
            if not cf.hasOccurred(self.settlement_date)
        ]


def _to_ql_date(d: date) -> Date:
    return Date(d.day, d.month, d.year)
