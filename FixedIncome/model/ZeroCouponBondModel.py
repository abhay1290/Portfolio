from sqlalchemy import Boolean, Column, ForeignKey, Integer

from FixedIncome.model.BondBase import BondBase


class ZeroCouponBondModel(BondBase):
    __tablename__ = 'zero_coupon_bonds'

    API_Path = "Zero_Coupon_Bonds"

    bond_id = Column(Integer, ForeignKey('bonds.id'), primary_key=True)

    # Whether accrued interest is applicable (some zero coupon bonds accrue interest differently)
    accrues_interest_flag = Column(Boolean, nullable=False, default=False)
