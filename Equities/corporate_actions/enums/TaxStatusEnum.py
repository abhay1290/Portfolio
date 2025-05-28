from enum import Enum


class TaxStatusEnum(Enum):
    TAXABLE = "TAXABLE"
    TAX_EXEMPT = "TAX_EXEMPT"
    TAX_DEFERRED = "TAX_DEFERRED"
    RETURN_OF_CAPITAL = "RETURN_OF_CAPITAL"
    OTHER = "OTHER"
