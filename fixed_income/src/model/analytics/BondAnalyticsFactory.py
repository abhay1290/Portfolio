from fixed_income.src.model.analytics.formulation import BondAnalyticsBase, CallableBondAnalytics, \
    FixedRateBondAnalytics, \
    FloatingRateBondAnalytics, PutableBondAnalytics, SinkingFundBondAnalytics, ZeroCouponBondAnalytics
from fixed_income.src.model.bonds import BondBase
from fixed_income.src.model.enums import BondTypeEnum


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
    elif bond.bond_type == BondTypeEnum.SINKING_FUND:
        return SinkingFundBondAnalytics(bond)
    else:
        raise ValueError(f"Unsupported bond type: {bond.bond_type}")
