# Custom Exceptions
class PortfolioServiceError(Exception):
    """Base exception for portfolio service errors"""
    pass


class PortfolioValidationError(PortfolioServiceError):
    """Validation-related errors"""
    pass


class PortfolioExistsError(PortfolioServiceError):
    """Portfolio already exists"""
    pass


class ConstituentValidationError(PortfolioServiceError):
    """Constituent validation failed"""
    pass


class PortfolioNotFoundError(PortfolioServiceError):
    """Portfolio not found"""
    pass
