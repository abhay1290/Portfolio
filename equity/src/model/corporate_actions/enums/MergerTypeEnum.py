from enum import Enum


class MergerTypeEnum(str, Enum):
    CASH = "CASH"
    STOCK = "STOCK"
    MIXED = "MIXED"
