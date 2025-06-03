from FixedIncome.src.api.bond_schema.CallableBondSchema import CallableBondRequest, CallableBondResponse
from FixedIncome.src.api.bond_schema.FixedRateBondSchema import FixedRateBondRequest, FixedRateBondResponse
from FixedIncome.src.api.bond_schema.FloatingRateBondSchema import FloatingRateBondRequest, FloatingRateBondResponse
from FixedIncome.src.api.bond_schema.PutableBondSchema import PutableBondRequest, PutableBondResponse
from FixedIncome.src.api.bond_schema.SinkingFundBondSchema import SinkingFundBondRequest, SinkingFundBondResponse
from FixedIncome.src.api.bond_schema.ZeroCouponBondSchema import ZeroCouponBondRequest, ZeroCouponBondResponse
from FixedIncome.src.api.routers.bond_crud_router import BondGenericRouter
from FixedIncome.src.model.bonds.BondBase import BondBase
from FixedIncome.src.model.bonds.CallableBondModel import CallableBondModel
from FixedIncome.src.model.bonds.FixedRateBondModel import FixedRateBondModel
from FixedIncome.src.model.bonds.FloatingRateBondModel import FloatingRateBondModel
from FixedIncome.src.model.bonds.PutableBondModel import PutableBondModel
from FixedIncome.src.model.bonds.SinkingFundBondModel import SinkingFundBondModel
from FixedIncome.src.model.bonds.ZeroCouponBondModel import ZeroCouponBondModel

zero_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=ZeroCouponBondModel,
    create_schema=ZeroCouponBondRequest,
    response_schema=ZeroCouponBondResponse,
    base_path=ZeroCouponBondModel.API_Path,
    tags=["Zero Coupon Bond"]
).router

fixed_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=FixedRateBondModel,
    create_schema=FixedRateBondRequest,
    response_schema=FixedRateBondResponse,
    base_path=FixedRateBondModel.API_Path,
    tags=["Fixed Rate Bond"]
).router

callable_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=CallableBondModel,
    create_schema=CallableBondRequest,
    response_schema=CallableBondResponse,
    base_path=CallableBondModel.API_Path,
    tags=["Callable Bond"]
).router

putable_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=PutableBondModel,
    create_schema=PutableBondRequest,
    response_schema=PutableBondResponse,
    base_path=PutableBondModel.API_Path,
    tags=["Putable Bond"]
).router

floater_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=FloatingRateBondModel,
    create_schema=FloatingRateBondRequest,
    response_schema=FloatingRateBondResponse,
    base_path=FloatingRateBondModel.API_Path,
    tags=["Floating Rate Bond"]
).router

sinking_bond_router = BondGenericRouter(
    bond_base_model=BondBase,
    model=SinkingFundBondModel,
    create_schema=SinkingFundBondRequest,
    response_schema=SinkingFundBondResponse,
    base_path=SinkingFundBondModel.API_Path,
    tags=["Sinking Fund Bond"]
).router
