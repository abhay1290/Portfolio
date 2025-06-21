from fixed_income.src.api.bond_schema.CallableBondSchema import CallableBondRequest, CallableBondResponse
from fixed_income.src.api.bond_schema.FixedRateBondSchema import FixedRateBondRequest, FixedRateBondResponse
from fixed_income.src.api.bond_schema.FloatingRateBondSchema import FloatingRateBondRequest, FloatingRateBondResponse
from fixed_income.src.api.bond_schema.PutableBondSchema import PutableBondRequest, PutableBondResponse
from fixed_income.src.api.bond_schema.SinkingFundBondSchema import SinkingFundBondRequest, SinkingFundBondResponse
from fixed_income.src.api.bond_schema.ZeroCouponBondSchema import ZeroCouponBondRequest, ZeroCouponBondResponse
from fixed_income.src.model.bonds import CallableBondModel, FixedRateBondModel, FloatingRateBondModel, PutableBondModel, \
    SinkingFundBondModel, ZeroCouponBondModel


def bond_schema_factory(bond_type: str):
    """Factory function to get the appropriate schema classes for a bond type"""
    schema_mapping = {
        'FIXED_COUPON': {
            'request': FixedRateBondRequest,
            'response': FixedRateBondResponse
        },
        'ZERO_COUPON': {
            'request': ZeroCouponBondRequest,
            'response': ZeroCouponBondResponse
        },
        'CALLABLE': {
            'request': CallableBondRequest,
            'response': CallableBondResponse
        },
        'PUTABLE': {
            'request': PutableBondRequest,
            'response': PutableBondResponse
        },
        'FLOATING': {
            'request': FloatingRateBondRequest,
            'response': FloatingRateBondResponse
        },
        'SINKING_FUND': {
            'request': SinkingFundBondRequest,
            'response': SinkingFundBondResponse
        }
    }

    if bond_type not in schema_mapping:
        raise ValueError(f"Unsupported bond_type: {bond_type}")

    return schema_mapping[bond_type]


def bond_model_factory(bond_type: str):
    """Factory function to get the appropriate bond model class"""
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
