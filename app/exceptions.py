class MarketForgeError(Exception):
    """Base domain exception."""


class DataContractError(MarketForgeError):
    """Raised when marketing data violates the contract."""


class InsufficientDataError(MarketForgeError):
    """Raised when an analysis cannot be estimated safely."""
