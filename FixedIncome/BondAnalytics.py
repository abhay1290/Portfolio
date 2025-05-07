# from datetime import date
#
# from QuantLib import *
#
# from FixedIncome.Bond import Bond
# from FixedIncome.BondTypeEnum import BondTypeEnum
# from FixedIncome.DayCountConventionEnum import DayCountConventionEnum
#
#
# def _to_ql_date(d: date) -> Date:
#     return Date(d.day, d.month, d.year)
#
#
# def _convert_day_count(dc_enum):
#     return {
#         DayCountConventionEnum.ACTUAL_360: Actual360(),
#         DayCountConventionEnum.ACTUAL_365: ActualActual(),
#         DayCountConventionEnum.THIRTY_360: Thirty360()
#     }[dc_enum]
#
#
# def _get_callable_putable_engine(discount_curve, maturity_date, steps=100):
#     # Hull-White short-rate model for tree-based pricing
#     model = HullWhite(discount_curve)
#     time_grid = TimeGrid(maturity_date, steps)
#     return TreeCallableFixedRateBondEngine(model, time_grid)
#
#
# class BondAnalytics:
#     def __init__(self, bond: Bond):
#         self.bond_obj = bond
#
#         self.symbol = bond.symbol
#         self.face_value = bond.face_value
#         self.coupon_rate = bond.coupon_rate
#         self.maturity_date = _to_ql_date(bond.maturity_date)
#         self.issue_date = _to_ql_date(bond.issue_date)
#         self.market_price = bond.market_price
#         self.bond_type = bond.bond_type
#         self.frequency = bond.frequency
#         self.credit_rating = bond.credit_rating
#         self.day_count_convention = _convert_day_count(bond.day_count_convention)
#         self.settlement_date = _to_ql_date(bond.settlement_date) if bond.settlement_date else Date.todaysDate()
#         self.call_schedule = bond.call_schedule
#         self.put_schedule = bond.put_schedule
#
#         self.calendar = TARGET()
#         self.convention = Following
#
#         # Coupon schedule
#         self.schedule = Schedule(
#             self.issue_date,
#             self.maturity_date,
#             Period(int(12 / self.frequency.value), Months),
#             self.calendar,
#             self.convention,
#             self.convention,
#             DateGeneration.Backward,
#             False
#         )
#
#         self.discount_curve = YieldTermStructureHandle(
#             FlatForward(self.settlement_date, QuoteHandle(SimpleQuote(0.05)), self.day_count_convention)
#         )
#
#         self.bond = self._create_bond()
#
#     def _create_bond(self):
#         if self.bond_type == BondTypeEnum.ZERO_COUPON:
#             return ZeroCouponBond(
#                 settlementDays=1,
#                 calendar=self.calendar,
#                 faceAmount=self.face_value,
#                 maturityDate=self.maturity_date,
#                 paymentConvention=self.convention,
#                 redemption=100.0,
#                 issueDate=self.issue_date
#             )
#
#         elif self.bond_type == BondTypeEnum.FIXED_COUPON:
#             return FixedRateBond(
#                 settlementDays=1,
#                 faceAmount=self.face_value,
#                 schedule=self.schedule,
#                 coupons=[self.coupon_rate],
#                 dayCounter=self.day_count_convention,
#                 paymentConvention=self.convention,
#                 redemption=100.0,
#                 issueDate=self.issue_date
#             )
#
#         elif self.bond_type in [BondTypeEnum.CALLABLE, BondTypeEnum.PUTABLE]:
#             callability_schedule = CallabilitySchedule()
#             if self.bond_type == BondTypeEnum.CALLABLE and self.call_schedule:
#                 for call_date, call_price in self.call_schedule:
#                     callability_schedule.append(Callability(
#                         BondPrice(call_price, BondPrice.Clean),
#                         Callability.Call,
#                         _to_ql_date(call_date)
#                     ))
#             if self.bond_type == BondTypeEnum.PUTABLE and self.put_schedule:
#                 for put_date, put_price in self.put_schedule:
#                     callability_schedule.append(Callability(
#                         BondPrice(put_price, BondPrice.Clean),
#                         Callability.Put,
#                         _to_ql_date(put_date)
#                     ))
#
#             callable_bond = CallableFixedRateBond(
#                 settlementDays=1,
#                 faceAmount=self.face_value,
#                 schedule=self.schedule,
#                 coupons=[self.coupon_rate],
#                 dayCounter=self.day_count_convention,
#                 paymentConvention=self.convention,
#                 redemption=100.0,
#                 issueDate=self.issue_date,
#                 putCallSchedule=callability_schedule
#             )
#
#             discount_curve = YieldTermStructureHandle(
#                 FlatForward(self.settlement_date,
#                             QuoteHandle(SimpleQuote(0.05)),
#                             self.day_count_convention))
#
#             engine = _get_callable_putable_engine(discount_curve, self.maturity_date)
#             callable_bond.setPricingEngine(engine)
#             return callable_bond
#
#         elif self.bond_type == BondTypeEnum.FLOATING:
#
#             discount_curve = YieldTermStructureHandle(
#                 FlatForward(self.settlement_date,
#                             QuoteHandle(SimpleQuote(0.05)),
#                             self.day_count_convention))
#
#             index = Euribor6M(discount_curve)
#             bond = FloatingRateBond(
#                 settlementDays=1,
#                 faceAmount=self.face_value,
#                 schedule=self.schedule,
#                 index=index,
#                 paymentConvention=self.convention,
#                 fixingDays=2,
#                 gearings=[1.0],
#                 spreads=[0.0],
#                 caps=[],
#                 floors=[],
#                 inArrears=False,
#                 redemption=100.0,
#                 issueDate=self.issue_date
#             )
#             bond.setPricingEngine(DiscountingBondEngine(discount_curve))
#             return bond
#
#         else:
#             raise ValueError(f"Unsupported bond type: {self.bond_type}")
#
#     def clean_price(self, yield_guess: float) -> float:
#         rate = YieldTermStructureHandle(
#             FlatForward(
#                 self.settlement_date,
#                 QuoteHandle(SimpleQuote(yield_guess)),
#                 self.day_count_convention
#             )
#         )
#         self.bond.setPricingEngine(DiscountingBondEngine(rate))
#         return self.bond.cleanPrice()
#
#     def dirty_price(self, yield_guess: float) -> float:
#         """
#         Dirty price includes accrued interest.
#         """
#         rate = YieldTermStructureHandle(
#             FlatForward(
#                 self.settlement_date,
#                 QuoteHandle(SimpleQuote(yield_guess)),
#                 self.day_count_convention
#             )
#         )
#         self.bond.setPricingEngine(DiscountingBondEngine(rate))
#         return self.bond.dirtyPrice()
#
#     def accrued_interest(self) -> float:
#         """
#         Calculate accrued interest of the bond.
#         """
#         return self.bond.accruedAmount(self.settlement_date)
#
#     def cashflows(self):
#         """
#         Return a list of tuples (date, amount) for the bond's future cashflows.
#         """
#         result = []
#         for cf in self.bond.cashflows():
#             if cf.date() >= self.settlement_date:
#                 result.append((cf.date().ISO(), cf.amount()))
#         return result
#
#     def yield_to_maturity(self) -> float:
#         return BondFunctions.yield_(
#             self.bond,
#             self.market_price,
#             self.day_count_convention,
#             Compounded,
#             self.frequency.value
#         )
#
#     def modified_duration(self) -> float:
#         ytm = self.yield_to_maturity()
#         return BondFunctions.duration(
#             self.bond,
#             ytm,
#             self.day_count_convention,
#             Compounded,
#             Duration.Modified,
#             self.frequency.value
#         )
#
#     def macaulay_duration(self) -> float:
#         ytm = self.yield_to_maturity()
#         return BondFunctions.duration(
#             self.bond,
#             ytm,
#             self.day_count_convention,
#             Compounded,
#             Duration.Macaulay,
#             self.frequency.value
#         )
#
#     def simple_duration(self) -> float:
#         ytm = self.yield_to_maturity()
#         return BondFunctions.duration(
#             self.bond,
#             ytm,
#             self.day_count_convention,
#             Compounded,
#             Duration.Simple,
#             self.frequency.value
#         )
#
#     def convexity(self) -> float:
#         ytm = self.yield_to_maturity()
#         return BondFunctions.convexity(
#             self.bond,
#             ytm,
#             self.day_count_convention,
#             Compounded,
#             self.frequency.value
#         )
#
#     def dv01(self, yield_guess: float) -> float:
#         """
#         DV01 (Dollar Value of 1 Basis Point) measures the price change for a 1bps change in yield.
#         """
#         price_at_ytm = self.clean_price(yield_guess)
#         price_at_ytm_plus_1bp = self.clean_price(yield_guess + 0.0001)  # 1bp = 0.0001
#         return (price_at_ytm - price_at_ytm_plus_1bp) * 10000  # Multiply by 10,000 to get the DV01 in dollar terms
