from enum import Enum


class DividendTypeEnum(str, Enum):
    CASH = "CASH"
    SPECIAL = "SPECIAL"
    STOCK = "STOCK"
    FINAL = "FINAL"
    LIQUIDATING = "LIQUIDATING"
