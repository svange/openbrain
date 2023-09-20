class OrmSessionNotFoundError(Exception):
    """Raised when a session is requested but not found in the database."""


class OrmProfileNotFoundError(Exception):
    """Raised when a profile is requested but not found in the database."""


class OrmAgentInstantiationError(Exception):
    """Raised when a session is requested but not found in the database."""


class OrmNotImplementedError(Exception):
    """Raised when the method is not yet implemented."""


class OrmSaveAgentConfigError(Exception):
    """Raised when saving an agent config fails."""
