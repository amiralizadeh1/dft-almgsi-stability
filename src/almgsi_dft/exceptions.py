"""Custom exceptions."""


class AlMgSiError(Exception):
    """Base package exception."""


class ConfigError(AlMgSiError):
    """Raised when configuration is malformed or unresolved."""


class MissingPseudopotentialError(ConfigError):
    """Raised when a required pseudopotential file is absent."""


class IncompatibleCalculationError(AlMgSiError):
    """Raised when incompatible calculations are combined."""


class RunError(AlMgSiError):
    """Raised for local execution errors."""
