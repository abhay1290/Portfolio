from FixedIncome.model.CallableBondModel import CallableBondModel
from FixedIncome.model.FixedRateBondModel import FixedRateBondModel
from FixedIncome.model.FloatingRateBondModel import FloatingRateBondModel
from FixedIncome.model.PutableBondModel import PutableBondModel
from FixedIncome.model.SinkingFundBondModel import SinkingFundBondModel
from FixedIncome.model.ZeroCouponBondModel import ZeroCouponBondModel


def bond_model_factory(bond_type: str):
    mapping = {
        'FIXED_COUPON': FixedRateBondModel,
        'ZERO_COUPON': ZeroCouponBondModel,
        'CALLABLE': CallableBondModel,
        'PUTABLE': PutableBondModel,
        'FLOATING': FloatingRateBondModel,
        'SINKING_FUND': SinkingFundBondModel
    }
    try:
        return mapping[bond_type]
    except KeyError:
        raise ValueError(f"Unsupported bond_type: {bond_type}")
