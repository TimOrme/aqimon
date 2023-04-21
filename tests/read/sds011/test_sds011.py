import pytest

from aqimon.read.sds011 import NovaPmReader
from aqimon.read.sds011.constants import ReportingMode, SleepState
from aqimon.read.sds011.exceptions import (
    IncorrectCommandException,
)
from .mock_device_serial import Sds011SerialEmulator


@pytest.fixture
def reader():
    # If you want to run these tests an integration you can replace the emulator here with a real serial device.
    # ser_dev = serial.Serial('/dev/ttyUSB0', timeout=2, baudrate=9600)
    ser_dev = Sds011SerialEmulator()

    # flush out the reader in case theres leftovers in the buffer
    ser_dev.read(10)

    reader = NovaPmReader(ser_dev=ser_dev, send_command_sleep=0)

    reader.wake()
    # We don't know if the device was in active or querying.  We must flush out the buffer from the above `wake`, if it
    # exists.
    ser_dev.read(10)

    reader.set_active_mode()
    reader.set_working_period(0)

    yield reader
    # Sleep the reader at the end so its not left on.
    reader.sleep()
    ser_dev.close()


def test_hammer_reporting_mode(reader: NovaPmReader):
    # Switch the modes
    reader.set_query_mode()
    reader.set_active_mode()

    # Set again in active mode
    reader.set_active_mode()

    # set it in query mode twice
    reader.set_query_mode()
    reader.set_query_mode()

    reader.request_reporting_mode()
    assert reader.query_reporting_mode().state == ReportingMode.QUERYING


def test_hammer_sleep_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.sleep()
    result = reader.query_sleep_state()
    assert result.state == SleepState.SLEEP

    reader.wake()
    reader.request_sleep_state()
    assert reader.query_sleep_state().state == SleepState.WORK
    reader.set_query_mode()
    reader.request_sleep_state()
    result = reader.query_sleep_state()
    assert result.state == SleepState.WORK


def test_hammer_sleep_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    reader.sleep()

    reader.wake()
    reader.set_active_mode()
    result = reader.query_data()
    assert result.pm25 > 0.0


def test_get_reporting_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.request_reporting_mode()
    result = reader.query_reporting_mode()
    assert result.state == ReportingMode.QUERYING


def test_get_reporting_mode_while_active_fails(reader: NovaPmReader):
    reader.set_active_mode()
    with pytest.raises(IncorrectCommandException):
        reader.query_reporting_mode()


def test_query_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    result = reader.query_data()
    assert 999 > result.pm25 > 0
    assert 999 > result.pm10 > 0


def test_query_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.request_data()
    result = reader.query_data()
    assert 999 > result.pm25 > 0
    assert 999 > result.pm10 > 0


def test_set_device_id_query_mode(reader: NovaPmReader):
    new_device_id = b"\xbb\xaa"
    reader.set_query_mode()
    reader.set_device_id(new_device_id)
    result = reader.query_device_id()
    assert result.device_id == new_device_id

    # Verify other commands also report correct ID
    reader.request_reporting_mode()
    result2 = reader.query_reporting_mode()
    assert result2.device_id == new_device_id


def test_sleep_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.sleep()
    result = reader.query_sleep_state()
    assert result.state == SleepState.SLEEP


def test_sleep_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    reader.sleep()


def test_wake_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.wake()
    result = reader.query_sleep_state()
    assert result.state == SleepState.WORK


def test_wake_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    reader.wake()


def test_get_sleep_state_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.wake()
    result = reader.query_sleep_state()
    assert result.state == SleepState.WORK


def test_get_sleep_state_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    with pytest.raises(IncorrectCommandException):
        reader.query_sleep_state()


def test_set_working_period_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.set_working_period(10)
    result = reader.query_working_period()
    assert result.interval == 10


def test_set_working_period_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    reader.set_working_period(10)


def test_get_working_period_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.set_working_period(10)
    result = reader.query_working_period()
    assert result.interval == 10


def test_get_working_period_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    with pytest.raises(IncorrectCommandException):
        reader.query_working_period()


def test_get_firmware_version_query_mode(reader: NovaPmReader):
    reader.set_query_mode()
    reader.request_firmware_version()
    result = reader.query_firmware_version()
    assert 99 >= result.year >= 0
    assert 12 >= result.month >= 1
    assert 31 >= result.day >= 1


def test_get_firmware_version_active_mode(reader: NovaPmReader):
    reader.set_active_mode()
    with pytest.raises(IncorrectCommandException):
        reader.query_firmware_version()
