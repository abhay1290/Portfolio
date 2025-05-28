from enum import Enum


class DividendTypeEnum(Enum):
    REGULAR = "REGULAR"
    SPECIAL = "SPECIAL"
    INTERIM = "INTERIM"
    FINAL = "FINAL"
    LIQUIDATING = "LIQUIDATING"
