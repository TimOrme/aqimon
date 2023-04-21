from serial import Serial
from aqimon.read.sds011.constants import (
    HEAD,
    TAIL,
    Commands,
    ReportingState,
    ReportingMode,
    ResponseTypes,
    SleepMode,
    SleepState,
    WorkingPeriodMode,
)
from dataclasses import dataclass


@dataclass(frozen=True)
class WriteData:
    """Simple wrapper for parsed write data."""

    raw_data: bytes
    raw_body_data: bytes
    command: Commands


class Sds011SerialEmulator(Serial):
    """Emulated SDS011 Serial Port.

    Behaves like the device itself, except is a bit more predictable in ACTIVE mode.
    """

    def __init__(self) -> None:
        """Create the emulator.

        Initializes to factory defaults.
        """
        super().__init__()
        self.response_buffer = b""
        self.response_type = b""
        self.query_mode = ReportingState.ACTIVE
        self.device_id = b"\x01\x01"
        self.sleep_state = SleepState.WORK
        self.working_period = bytes([0])
        self.firmware_year = bytes([1])
        self.firmware_month = bytes([2])
        self.firmware_day = bytes([3])

    def open(self):
        """No-op open."""
        pass

    def close(self):
        """No-op close."""
        pass

    def read(self, size: int = 1) -> bytes:
        """Read from the emulator."""
        if self.query_mode == ReportingState.ACTIVE:
            # If in active mode, always return query response.
            return self._get_query_response()
        else:
            response = self.response_buffer
            self.response_buffer = b""
            return response

    def _generate_read(self, response_type: ResponseTypes, cmd: bytes) -> bytes:
        """Generate a read command, with wrapper and checksum."""
        cmd_and_id = cmd + self.device_id
        return HEAD + response_type.value + cmd_and_id + read_checksum(cmd_and_id) + TAIL

    def write(self, data: bytes) -> int:
        """Write to the emulator."""
        last_write = parse_write_data(data)
        self.response_type = last_write.raw_body_data[1:2]
        if last_write.command == Commands.SET_REPORTING_MODE:
            if ReportingMode(last_write.raw_body_data[1:2]) == ReportingMode.SET_MODE:
                self.query_mode = ReportingState(last_write.raw_body_data[2:3])
            self.response_buffer = self._set_reporting_mode_response()
        elif last_write.command == Commands.QUERY:
            self.response_buffer = self._get_query_response()
        elif last_write.command == Commands.SET_DEVICE_ID:
            self.device_id = last_write.raw_body_data[11:13]
            self.response_buffer = self._set_device_id_response()
        elif last_write.command == Commands.SET_SLEEP:
            if SleepMode(last_write.raw_body_data[1:2]) == SleepMode.SET_MODE:
                self.sleep_state = SleepState(last_write.raw_body_data[2:3])
            self.response_buffer = self._set_sleep_response()
        elif last_write.command == Commands.SET_WORKING_PERIOD:
            if WorkingPeriodMode(last_write.raw_body_data[1:2]) == WorkingPeriodMode.SET_MODE:
                self.working_period = last_write.raw_body_data[2:3]
            self.response_buffer = self._set_working_period_response()
        elif last_write.command == Commands.CHECK_FIRMWARE_VERSION:
            self.response_buffer = self._check_firmware_response()
        return len(data)

    def _get_query_response(self) -> bytes:
        return self._generate_read(ResponseTypes.QUERY_RESPONSE, b"\x19\x00\x64\x00")

    def _set_reporting_mode_response(self) -> bytes:
        return self._generate_read(
            ResponseTypes.GENERAL_RESPONSE,
            Commands.SET_REPORTING_MODE.value + self.response_type + self.query_mode.value + b"\x00",
        )

    def _set_device_id_response(self) -> bytes:
        return self._generate_read(ResponseTypes.GENERAL_RESPONSE, Commands.SET_DEVICE_ID.value + (b"\x00" * 3))

    def _set_sleep_response(self) -> bytes:
        return self._generate_read(
            ResponseTypes.GENERAL_RESPONSE,
            Commands.SET_SLEEP.value + self.response_type + self.sleep_state.value + b"\x00",
        )

    def _set_working_period_response(self) -> bytes:
        return self._generate_read(
            ResponseTypes.GENERAL_RESPONSE,
            Commands.SET_WORKING_PERIOD.value + self.response_type + self.working_period + b"\x00",
        )

    def _check_firmware_response(self) -> bytes:
        return self._generate_read(
            ResponseTypes.GENERAL_RESPONSE,
            Commands.CHECK_FIRMWARE_VERSION.value + self.firmware_year + self.firmware_month + self.firmware_day,
        )


def read_checksum(data: bytes) -> bytes:
    """Generate a checksum for the data bytes of a command."""
    if len(data) != 6:
        raise AttributeError("Invalid checksum length.")
    return bytes([sum(d for d in data) % 256])


def parse_write_data(data: bytes) -> WriteData:
    """Parse write data from the emulator into a neater wrapper."""
    if len(data) != 19:
        raise AttributeError("Data is wrong size.")
    return WriteData(raw_data=data, raw_body_data=data[2:15], command=Commands(data[2:3]))
