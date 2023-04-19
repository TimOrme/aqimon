from serial import Serial
from typing import Optional
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
        self.last_write: Optional[WriteData] = None
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
        if self.last_write is not None:
            if self.query_mode == ReportingState.ACTIVE:
                # Admittedly, this command sometimes fails on the device as well. It's the only one that seems to fairly
                # consistently return in ACTIVE mode though, so the emulator does the same.
                if (
                    self.last_write.command == Commands.SET_REPORTING_MODE
                    and ReportingMode(self.last_write.raw_body_data[1:2]) == ReportingMode.SET_MODE
                ):
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE,
                        Commands.SET_REPORTING_MODE.value
                        + self.last_write.raw_body_data[1:2]
                        + self.query_mode.value
                        + b"\x00",
                    )

                # If in active mode, almost always return query response.
                return self._generate_read(ResponseTypes.QUERY_RESPONSE, b"\x19\x00\x64\x00")
            else:
                if self.last_write.command == Commands.QUERY:
                    return self._generate_read(ResponseTypes.QUERY_RESPONSE, b"\x19\x00\x64\x00")
                elif self.last_write.command == Commands.SET_REPORTING_MODE:
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE,
                        Commands.SET_REPORTING_MODE.value
                        + self.last_write.raw_body_data[1:2]
                        + self.query_mode.value
                        + b"\x00",
                    )
                elif self.last_write.command == Commands.SET_DEVICE_ID:
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE, Commands.SET_DEVICE_ID.value + (b"\x00" * 3)
                    )
                elif self.last_write.command == Commands.SET_SLEEP:
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE,
                        Commands.SET_SLEEP.value
                        + self.last_write.raw_body_data[1:2]
                        + self.sleep_state.value
                        + b"\x00",
                    )
                elif self.last_write.command == Commands.SET_WORKING_PERIOD:
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE,
                        Commands.SET_WORKING_PERIOD.value
                        + self.last_write.raw_body_data[1:2]
                        + self.working_period
                        + b"\x00",
                    )
                elif self.last_write.command == Commands.CHECK_FIRMWARE_VERSION:
                    return self._generate_read(
                        ResponseTypes.GENERAL_RESPONSE,
                        Commands.CHECK_FIRMWARE_VERSION.value
                        + self.firmware_year
                        + self.firmware_month
                        + self.firmware_day,
                    )
        return b""

    def _generate_read(self, response_type: ResponseTypes, cmd: bytes):
        """Generate a read command, with wrapper and checksum."""
        cmd_and_id = cmd + self.device_id
        return HEAD + response_type.value + cmd_and_id + read_checksum(cmd_and_id) + TAIL

    def write(self, data: bytes) -> int:
        """Write to the emulator."""
        self.last_write = parse_write_data(data)
        if (
            self.last_write.command == Commands.SET_REPORTING_MODE
            and ReportingMode(self.last_write.raw_body_data[1:2]) == ReportingMode.SET_MODE
        ):
            self.query_mode = ReportingState(self.last_write.raw_body_data[2:3])
        elif self.last_write.command == Commands.SET_DEVICE_ID:
            self.device_id = self.last_write.raw_body_data[11:13]
        elif (
            self.last_write.command == Commands.SET_SLEEP
            and SleepMode(self.last_write.raw_body_data[1:2]) == SleepMode.SET_MODE
        ):
            self.sleep_state = SleepState(self.last_write.raw_body_data[2:3])
        elif (
            self.last_write.command == Commands.SET_WORKING_PERIOD
            and WorkingPeriodMode(self.last_write.raw_body_data[1:2]) == WorkingPeriodMode.SET_MODE
        ):
            self.working_period = self.last_write.raw_body_data[2:3]
        return len(data)


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
