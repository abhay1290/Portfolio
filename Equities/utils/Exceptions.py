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


class ProcessingLockError(CorporateActionError):
    """Exception raised when equity is locked for processing"""
    pass


class RollbackError(CorporateActionError):
    """Exception raised during rollback operations"""
    pass


class ExecutorNotFoundError(CorporateActionError):
    """Exception raised when no executor found for corporate action type"""
    pass
