"""All exception classes for the SDS011."""


class Sds011Exception(Exception):
    """Base exception for SDS011 device."""

    pass


class ChecksumFailedException(Sds011Exception):
    """Thrown if the checksum value in a response is incorrect."""

    def __init__(self, expected: int, actual: int):
        """Create exception."""
        super().__init__()
        self.expected = expected
        self.actual = actual


class IncorrectCommandException(Sds011Exception):
    """Thrown if the command ID in a response is incorrect."""

    def __init__(self, expected: int, actual: int):
        """Create exception."""
        super().__init__(f"Expected command {expected}, found {actual}")
        self.expected = expected
        self.actual = actual


class IncorrectCommandCodeException(Sds011Exception):
    """Thrown if the command code in a response is incorrect."""

    def __init__(self, expected: int, actual: int):
        """Create exception."""
        super().__init__(f"Expected code {expected}, found {actual}")
        self.expected = expected
        self.actual = actual


class IncorrectWrapperException(Sds011Exception):
    """Thrown if the wrapper of a response (either HEAD or TAIL) is incorrect."""

    pass


class IncompleteReadException(Sds011Exception):
    """Thrown if the device didn't return complete data when asking for a response."""

    pass


class QueryInActiveModeException(Sds011Exception):
    """Thrown if any query is issued while the device is in ACTIVE mode."""

    pass


class InvalidDeviceIdException(Sds011Exception):
    """Thrown if the trying to set the device ID on an invalid device."""

    pass
