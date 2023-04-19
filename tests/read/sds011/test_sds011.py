import pytest

from aqimon.read.sds011 import NovaPmReader
from aqimon.read.sds011.constants import ReportingState, SleepState
from aqimon.read.sds011.exceptions import QueryInActiveModeException
from .mock_device_serial import Sds011SerialEmulator


@pytest.fixture
def reader():
    # In a theoretical world, you could replace the emulator here with a true serial device, and run these as
    # integration tests.  However, in practice, the behavior of ACTIVE mode is too inconsistent for many of these tests
    # to behave reliably.
    ser_dev = Sds011SerialEmulator()
    reader = NovaPmReader(ser_dev=ser_dev)
    try:
        reader.wake()
    except QueryInActiveModeException:
        pass
    reader.set_reporting_mode(ReportingState.QUERYING)
    reader.set_working_period(0)
    reader.set_reporting_mode(ReportingState.ACTIVE)
    yield reader
    ser_dev.close()


def test_set_reporting_mode(reader: NovaPmReader):
    result = reader.set_reporting_mode(ReportingState.QUERYING)
    assert result.state == ReportingState.QUERYING


def test_get_reporting_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.get_reporting_mode()
    assert result.state == ReportingState.QUERYING


def test_get_reporting_mode_while_active_fails(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.get_reporting_mode()


def test_query_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    result = reader.query()
    assert 999 > result.pm25 > 0
    assert 999 > result.pm10 > 0


def test_query_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.query()
    assert 999 > result.pm25 > 0
    assert 999 > result.pm10 > 0


def test_set_device_id(reader: NovaPmReader):
    new_device_id = b"\xbb\xaa"
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.set_device_id(new_device_id)
    assert result.device_id == new_device_id

    # Verify other commands also report correct ID
    result2 = reader.get_reporting_mode()
    assert result2.device_id == new_device_id


def test_sleep_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.sleep()
    assert result.state == SleepState.SLEEP


def test_sleep_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.sleep()


def test_wake_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.wake()
    assert result.state == SleepState.WORK


def test_wake_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.wake()


def test_get_sleep_state_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    reader.wake()
    result = reader.get_sleep_state()
    assert result.state == SleepState.WORK


def test_get_sleep_state_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.get_sleep_state()


def test_set_working_period_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.set_working_period(10)
    assert result.interval == 10


def test_set_working_period_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.set_working_period(10)


def test_get_working_period_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    reader.set_working_period(10)
    result = reader.get_working_period()
    assert result.interval == 10


def test_get_working_period_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.get_working_period()


def test_get_firmware_version_query_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.QUERYING)
    result = reader.get_firmware_version()
    assert 99 >= result.year >= 0
    assert 12 >= result.month >= 1
    assert 31 >= result.day >= 1


def test_get_firmware_version_active_mode(reader: NovaPmReader):
    reader.set_reporting_mode(ReportingState.ACTIVE)
    with pytest.raises(QueryInActiveModeException):
        reader.get_firmware_version()
