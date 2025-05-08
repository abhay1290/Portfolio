from FixedIncome.analytics.BondAnalyticsBase import BondAnalyticsBase
from FixedIncome.analytics.CallableBondAnalytics import CallableBondAnalytics
from FixedIncome.analytics.FixedRateBondAnalytics import FixedRateBondAnalytics
from FixedIncome.analytics.FloatingRateBondAnalytics import FloatingRateBondAnalytics
from FixedIncome.analytics.PutableBondAnalytics import PutableBondAnalytics
from FixedIncome.analytics.ZeroCouponBondAnalytics import ZeroCouponBondAnalytics
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
