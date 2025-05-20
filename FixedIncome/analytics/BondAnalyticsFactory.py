from FixedIncome.analytics.formulation.BondAnalyticsBase import BondAnalyticsBase
from FixedIncome.analytics.formulation.CallableBondAnalytics import CallableBondAnalytics
from FixedIncome.analytics.formulation.FixedRateBondAnalytics import FixedRateBondAnalytics
from FixedIncome.analytics.formulation.FloatingRateBondAnalytics import FloatingRateBondAnalytics
from FixedIncome.analytics.formulation.PutableBondAnalytics import PutableBondAnalytics
from FixedIncome.analytics.formulation.ZeroCouponBondAnalytics import ZeroCouponBondAnalytics
from FixedIncome.enums.BondTypeEnum import BondTypeEnum
from FixedIncome.model.BondBase import BondBase


def bond_analytics_factory(bond: BondBase) -> BondAnalyticsBase:
    if bond.bond_type == BondTypeEnum.ZERO_COUPON:
        return ZeroCouponBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.FIXED_COUPON:
        return FixedRateBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.CALLABLE:
        return CallableBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.PUTABLE:
        return PutableBondAnalytics(bond)
    elif bond.bond_type == BondTypeEnum.FLOATING:
        return FloatingRateBondAnalytics(bond)
    else:
        raise ValueError(f"Unsupported bond type: {bond.bond_type}")
