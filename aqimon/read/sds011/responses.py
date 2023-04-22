"""Response objects for SDS011.

Creates and validates typed classes from binary responses from the device.
"""
from .constants import (
    HEAD,
    TAIL,
    Command,
    ResponseType,
    SleepState,
    OperationType,
    ReportingMode,
)
from .exceptions import (
    ChecksumFailedException,
    IncorrectCommandException,
    IncorrectCommandCodeException,
    IncorrectWrapperException,
    IncompleteReadException,
)


class ReadResponse:
    """Generic read response object for responses from SDS011."""

    def __init__(self, data: bytes, command_code: Command, response_type: ResponseType = ResponseType.GENERAL_RESPONSE):
        """Create a read response."""
        if len(data) != 10:
            raise IncompleteReadException()

        self.head = data[0:1]
        self.cmd_id = data[1:2]
        self.data = data[2:8]
        self.device_id = data[6:8]
        self.checksum: int = data[8]
        self.tail = data[9:10]
        self.expected_command_code = command_code
        self.expected_response_type = response_type
        # Check it!
        self.verify()

    def verify(self):
        """Verify the read data."""
        if self.head != HEAD:
            raise IncorrectWrapperException()
        if self.tail != TAIL:
            raise IncorrectWrapperException()
        if self.checksum != self.calc_checksum():
            raise ChecksumFailedException(expected=self.checksum, actual=self.calc_checksum())
        if self.cmd_id != self.expected_response_type.value:
            raise IncorrectCommandException(expected=self.expected_response_type.value, actual=self.cmd_id)

        # Query responses don't validate the command code
        if (
            self.expected_response_type != ResponseType.QUERY_RESPONSE
            and bytes([self.data[0]]) != self.expected_command_code.value
        ):
            raise IncorrectCommandCodeException(expected=self.expected_command_code.value, actual=self.data[0])

    def calc_checksum(self) -> int:
        """Calculate the checksum for the read data."""
        return sum(d for d in self.data) % 256


class QueryReadResponse(ReadResponse):
    """Query read response."""

    def __init__(self, data: bytes):
        """Create a query read response."""
        super().__init__(data, command_code=Command.QUERY, response_type=ResponseType.QUERY_RESPONSE)

        self.pm25: float = int.from_bytes(data[2:4], byteorder="little") / 10
        self.pm10: float = int.from_bytes(data[4:6], byteorder="little") / 10


class ReportingModeReadResponse(ReadResponse):
    """Reporting mode response."""

    def __init__(self, data: bytes):
        """Create a reporting mode response."""
        super().__init__(data, command_code=Command.SET_REPORTING_MODE)
        self.operation_type = OperationType(self.data[1:2])
        self.state = ReportingMode(self.data[2:3])


class DeviceIdResponse(ReadResponse):
    """Device ID response."""

    def __init__(self, data: bytes):
        """Create a device ID response."""
        super().__init__(data, command_code=Command.SET_DEVICE_ID)


class SleepWakeReadResponse(ReadResponse):
    """Sleep/Wake Response."""

    def __init__(self, data: bytes):
        """Create a sleep/wake response."""
        super().__init__(data, command_code=Command.SET_SLEEP)
        self.operation_type = OperationType(self.data[1:2])
        self.state = SleepState(self.data[2:3])


class WorkingPeriodReadResponse(ReadResponse):
    """Working period response."""

    def __init__(self, data: bytes):
        """Create a working period response."""
        super().__init__(data, command_code=Command.SET_WORKING_PERIOD)
        self.operation_type = OperationType(self.data[1:2])
        self.interval: int = self.data[2]


class CheckFirmwareReadResponse(ReadResponse):
    """Firmware response."""

    def __init__(self, data: bytes):
        """Create a firmware response."""
        super().__init__(data, command_code=Command.CHECK_FIRMWARE_VERSION)
        self.year = self.data[1]
        self.month = self.data[2]
        self.day = self.data[3]
