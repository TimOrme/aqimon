"""Nova PM SDS011 Reader module.

Device: https://www.amazon.com/SDS011-Quality-Detection-Conditioning-Monitor/dp/B07FSDMRR5

Spec: https://cdn.sparkfun.com/assets/parts/1/2/2/7/5/Laser_Dust_Sensor_Control_Protocol_V1.3.pdf
Spec: https://cdn-reichelt.de/documents/datenblatt/X200/SDS011-DATASHEET.pdf
"""

import serial
import time
from .responses import (
    QueryReadResponse,
    ReportingModeReadResponse,
    SleepWakeReadResponse,
    DeviceIdResponse,
    CheckFirmwareReadResponse,
    WorkingPeriodReadResponse,
)
from . import constants as con
from .exceptions import IncompleteReadException, IncorrectCommandException, IncorrectCommandCodeException


class NovaPmReader:
    """NOVA PM SDS011 Reader."""

    def __init__(self, ser_dev: serial.Serial, send_command_sleep: int = 1):
        """Create the device."""
        self.ser = ser_dev
        self.send_command_sleep = send_command_sleep

    def request_data(self) -> None:
        """Request device to return pollutant data."""
        cmd = con.Command.QUERY.value + (b"\x00" * 12) + con.ALL_SENSOR_ID
        self._send_command(cmd)

    def query_data(self) -> QueryReadResponse:
        """Query the device for pollutant data."""
        return QueryReadResponse(self._read_response())

    def request_reporting_mode(self) -> None:
        """Request device to return the current reporting mode."""
        cmd = (
            con.Command.SET_REPORTING_MODE.value
            + con.OperationType.QUERY.value
            + con.ReportingMode.ACTIVE.value
            + (b"\x00" * 10)
            + con.ALL_SENSOR_ID
        )
        self._send_command(cmd)

    def query_reporting_mode(self) -> ReportingModeReadResponse:
        """Get the current reporting mode of the device."""
        return ReportingModeReadResponse(self._read_response())

    def set_active_mode(self) -> None:
        """Set the reporting mode to active."""
        self._set_reporting_mode(con.ReportingMode.ACTIVE)
        try:
            self.query_reporting_mode()
        except IncorrectCommandException:
            pass
        except IncompleteReadException:
            pass

    def set_query_mode(self) -> None:
        """Set the reporting mode to querying."""
        self._set_reporting_mode(con.ReportingMode.QUERYING)
        try:
            self.query_reporting_mode()
        except IncorrectCommandException:
            pass
        except IncompleteReadException:
            pass
        except IncorrectCommandCodeException:
            pass

    def _set_reporting_mode(self, reporting_mode: con.ReportingMode) -> None:
        """Set the reporting mode, either ACTIVE or QUERYING.

        ACTIVE mode means the device will always return a Query command response when data is asked for, regardless of
        what command was sent.

        QUERYING mode means the device will only return responses to submitted commands, even for Query commands.

        ACTIVE mode is the factory default, but generally, QUERYING mode is preferrable for the longevity of the device.
        """
        cmd = (
            con.Command.SET_REPORTING_MODE.value
            + con.OperationType.SET_MODE.value
            + reporting_mode.value
            + (b"\x00" * 10)
            + con.ALL_SENSOR_ID
        )
        self._send_command(cmd)
        # Switching between reporting modes is finicky; resetting the serial connection seems to address issues.
        self.ser.close()
        self.ser.open()

    def request_sleep_state(self) -> None:
        """Get the current sleep state."""
        cmd = con.Command.SET_SLEEP.value + con.OperationType.QUERY.value + b"\x00" + (b"\x00" * 10) + con.ALL_SENSOR_ID
        self._send_command(cmd)

    def query_sleep_state(self) -> SleepWakeReadResponse:
        """Get the current sleep state."""
        return SleepWakeReadResponse(self._read_response())

    def set_sleep_state(self, sleep_state: con.SleepState) -> None:
        """Set the sleep state, either wake or sleep."""
        cmd = (
            con.Command.SET_SLEEP.value
            + con.OperationType.SET_MODE.value
            + sleep_state.value
            + (b"\x00" * 10)
            + con.ALL_SENSOR_ID
        )
        self._send_command(cmd)

    def sleep(self) -> None:
        """Put the device to sleep, turning off fan and diode."""
        self.set_sleep_state(con.SleepState.SLEEP)

    def wake(self) -> None:
        """Wake the device up to start reading."""
        self.set_sleep_state(con.SleepState.WORK)

    def safe_wake(self) -> None:
        """Wake the device up, if you don't know what mode its in.

        This operates as a fire-and-forget, even in query mode.  You shouldn't have to (and can't) query for a response
        after this command.
        """
        self.wake()
        # If we were in query mode, this would flush out the response.  If in active mode, this would be return read
        # data, but we don't care.
        self.ser.read(10)

    def set_device_id(self, device_id: bytes, target_device_id: bytes = con.ALL_SENSOR_ID) -> None:
        """Set the device ID."""
        if len(device_id) != 2 or len(target_device_id) != 2:
            raise AttributeError(f"Device ID must be 4 bytes, found {len(device_id)}, and {len(target_device_id)}")
        cmd = con.Command.SET_DEVICE_ID.value + (b"\x00" * 10) + device_id + target_device_id
        self._send_command(cmd)

    def query_device_id(self) -> DeviceIdResponse:
        """Set the device ID."""
        return DeviceIdResponse(self._read_response())

    def request_working_period(self) -> None:
        """Retrieve the current working period for the device."""
        cmd = con.Command.SET_WORKING_PERIOD.value + con.OperationType.QUERY.value + (b"\x00" * 11) + con.ALL_SENSOR_ID
        self._send_command(cmd)

    def query_working_period(self) -> WorkingPeriodReadResponse:
        """Retrieve the current working period for the device."""
        return WorkingPeriodReadResponse(self._read_response())

    def set_working_period(self, working_period: int) -> None:
        """Set the working period for the device.

        Working period must be between 0 and 30.

        0 means the device will read continuously.
        Any value 1-30 means the device will wake and read for 30 seconds every n*60-30 seconds.
        """
        if 0 >= working_period >= 30:
            raise AttributeError("Working period must be between 0 and 30")
        cmd = (
            con.Command.SET_WORKING_PERIOD.value
            + con.OperationType.SET_MODE.value
            + bytes([working_period])
            + (b"\x00" * 10)
            + con.ALL_SENSOR_ID
        )
        self._send_command(cmd)

    def request_firmware_version(self) -> None:
        """Retrieve the firmware version from the device."""
        cmd = con.Command.CHECK_FIRMWARE_VERSION.value + (b"\x00" * 12) + con.ALL_SENSOR_ID
        self._send_command(cmd)

    def query_firmware_version(self) -> CheckFirmwareReadResponse:
        """Retrieve the firmware version from the device."""
        return CheckFirmwareReadResponse(self._read_response())

    def _send_command(self, cmd: bytes):
        """Send a command to the device as bytes."""
        head = con.HEAD + con.SUBMIT_TYPE
        full_command = head + cmd + bytes([self._cmd_checksum(cmd)]) + con.TAIL
        if len(full_command) != 19:
            raise Exception(f"Command length must be 19, but was {len(full_command)}")
        self.ser.write(full_command)
        time.sleep(self.send_command_sleep)

    def _read_response(self) -> bytes:
        """Read a response from the device."""
        result = self.ser.read(10)
        if len(result) != 10:
            raise IncompleteReadException(len(result))
        return result

    def _cmd_checksum(self, data: bytes) -> int:
        """Generate a checksum for the data bytes of a command."""
        if len(data) != 15:
            raise AttributeError("Invalid checksum length.")
        return sum(d for d in data) % 256


class QueryModeReader:
    """Reader working in query mode."""

    def __init__(self, ser_dev: serial.Serial, send_command_sleep: int = 1):
        """Create the device."""
        self.base_reader = NovaPmReader(ser_dev=ser_dev, send_command_sleep=send_command_sleep)
        self.base_reader.safe_wake()
        self.base_reader.set_query_mode()

    def query(self) -> QueryReadResponse:
        """Query the device for pollutant data."""
        self.base_reader.request_data()
        return self.base_reader.query_data()

    def get_reporting_mode(self) -> ReportingModeReadResponse:
        """Get the current reporting mode of the device."""
        self.base_reader.request_reporting_mode()
        return self.base_reader.query_reporting_mode()

    def get_sleep_state(self) -> SleepWakeReadResponse:
        """Get the current sleep state."""
        self.base_reader.request_sleep_state()
        return self.base_reader.query_sleep_state()

    def sleep(self) -> SleepWakeReadResponse:
        """Put the device to sleep, turning off fan and diode."""
        self.base_reader.sleep()
        return self.base_reader.query_sleep_state()

    def wake(self) -> SleepWakeReadResponse:
        """Wake the device up to start reading."""
        self.base_reader.wake()
        return self.base_reader.query_sleep_state()

    def set_device_id(self, device_id: bytes, target_device_id: bytes = con.ALL_SENSOR_ID) -> DeviceIdResponse:
        """Set the device ID."""
        self.base_reader.set_device_id(device_id, target_device_id)
        return self.base_reader.query_device_id()

    def get_working_period(self) -> WorkingPeriodReadResponse:
        """Retrieve the current working period for the device."""
        self.base_reader.request_working_period()
        return self.base_reader.query_working_period()

    def set_working_period(self, working_period: int) -> WorkingPeriodReadResponse:
        """Set the working period for the device.

        Working period must be between 0 and 30.

        0 means the device will read continuously.
        Any value 1-30 means the device will wake and read for 30 seconds every n*60-30 seconds.
        """
        self.base_reader.set_working_period(working_period)
        return self.base_reader.query_working_period()

    def get_firmware_version(self) -> CheckFirmwareReadResponse:
        """Retrieve the firmware version from the device."""
        self.base_reader.request_firmware_version()
        return self.base_reader.query_firmware_version()


class ActiveModeReader:
    """Active Mode Reader.

    Use with caution! Active mode is unpredictable.  Query mode is much preferred.
    """

    def __init__(self, ser_dev: serial.Serial, send_command_sleep: int = 2):
        """Create the device."""
        self.base_reader = NovaPmReader(ser_dev=ser_dev, send_command_sleep=send_command_sleep)
        self.ser_dev = ser_dev
        self.base_reader.safe_wake()
        self.base_reader.set_active_mode()

    def query(self) -> QueryReadResponse:
        """Query the device for pollutant data."""
        return self.base_reader.query_data()

    def sleep(self) -> None:
        """Put the device to sleep, turning off fan and diode."""
        self.base_reader.sleep()

        # Sleep seems to behave very strangely in active mode.  It continually outputs data for old commands for quite
        # a while before eventually having nothing to report.  This forces it to "drain" whatever it was doing before
        # returning, but also feels quite dangerous.
        while len(self.ser_dev.read(10)) == 10:
            pass

    def wake(self) -> None:
        """Wake the device up to start reading."""
        self.base_reader.wake()
        self.ser_dev.read(10)

    def set_device_id(self, device_id: bytes, target_device_id: bytes = con.ALL_SENSOR_ID) -> None:
        """Set the device ID."""
        self.base_reader.set_device_id(device_id, target_device_id)
        self.ser_dev.read(10)

    def set_working_period(self, working_period: int) -> None:
        """Set the working period for the device.

        Working period must be between 0 and 30.

        0 means the device will read continuously.
        Any value 1-30 means the device will wake and read for 30 seconds every n*60-30 seconds.
        """
        self.base_reader.set_working_period(working_period)
        self.ser_dev.read(10)
