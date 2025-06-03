from fixed_income.src.model.bonds import CallableBondModel, FixedRateBondModel, FloatingRateBondModel, PutableBondModel, \
    SinkingFundBondModel, ZeroCouponBondModel


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
