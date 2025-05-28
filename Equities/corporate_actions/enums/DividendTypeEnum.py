from enum import Enum


class DividendTypeEnum(str, Enum):
    CASH = "CASH"
    SPECIAL = "SPECIAL"
    INTERIM = "INTERIM"
    FINAL = "FINAL"
    LIQUIDATING = "LIQUIDATING"
