from enum import Enum


class AssetClassEnum(str, Enum):
    EQUITY = "EQUITY"
    FIXED_INCOME = "FIXED_INCOME"
    MULTI_ASSET = "MULTI_ASSET"
