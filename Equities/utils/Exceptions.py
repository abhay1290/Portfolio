class CorporateActionError(Exception):
    """Base exception for corporate action related errors"""
    pass


class EquityValidationError(CorporateActionError):
    """Exception raised for equity validation errors"""
    pass


class CorporateActionValidationError(CorporateActionError):
    """Exception raised for corporate action validation errors"""
    pass


class DividendValidationError(CorporateActionValidationError):
    """Exception raised for dividend validation errors"""
    pass


class SpecialDividendValidationError(CorporateActionValidationError):
    """Exception raised for special dividend validation errors"""
    pass


class DistributionValidationError(CorporateActionValidationError):
    """Exception raised for distribution validation errors"""
    pass


class ReturnOfCapitalValidationError(CorporateActionValidationError):
    """Exception raised for return of capital validation errors"""
    pass


class AcquisitionValidationError(CorporateActionValidationError):
    """Exception raised for a  Acquisition validation errors"""
    pass


class ExchangeOfferValidationError(CorporateActionValidationError):
    """Exception raised for a ExchangeOffer validation errors"""
    pass


class MergerValidationError(CorporateActionValidationError):
    """Exception raised for a Merger validation errors"""
    pass


class TenderOfferValidationError(CorporateActionValidationError):
    """Exception raised for a TenderOffer validation errors"""
    pass


class ProcessingLockError(CorporateActionError):
    """Exception raised when equity is locked for processing"""
    pass


class RollbackError(CorporateActionError):
    """Exception raised during rollback operations"""
    pass


class ExecutorNotFoundError(CorporateActionError):
    """Exception raised when no executor found for corporate action type"""
    pass
