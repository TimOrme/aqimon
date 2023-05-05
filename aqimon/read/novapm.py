"""Nova PM SDS011 Reader module.

https://www.amazon.com/SDS011-Quality-Detection-Conditioning-Monitor/dp/B07FSDMRR5
"""
import asyncio

from . import AqiRead, ReaderState, ReaderStatus
import serial
from typing import Union
from sds011lib import SDS011QueryReader
from statistics import mean


class OpinionatedReader:
    """NOVA PM SDS011 Reader."""

    def __init__(
        self,
        ser_dev: Union[str, serial.Serial],
        warm_up_secs: int = 15,
        iterations: int = 5,
        sleep_time: int = 3,
        command_wait_time: int = 15,
    ):
        """Create the device."""
        if isinstance(ser_dev, str):
            ser_dev = serial.Serial(ser_dev, timeout=2)

        self.reader = SDS011QueryReader(ser_dev=ser_dev, send_command_sleep=command_wait_time)

        # Initial the reader to be in the mode we want.
        self.reader.wake()
        self.reader.set_working_period(0)

        self.warm_up_secs = warm_up_secs
        self.iterations = iterations
        self.sleep_time = sleep_time

        self.state = ReaderState(ReaderStatus.IDLE, None)

    async def read(self) -> AqiRead:
        """Read from the device."""
        try:
            self.reader.wake()
            self.state = ReaderState(ReaderStatus.WARM_UP, None)
            await asyncio.sleep(self.warm_up_secs)
            self.state = ReaderState(ReaderStatus.READING, None)
            pm25_reads = []
            pm10_reads = []
            for x in range(0, self.iterations):
                await asyncio.sleep(self.sleep_time)
                result = self.reader.query()
                pm25_reads.append(result.pm25)
                pm10_reads.append(result.pm10)
            self.reader.sleep()
            self.state = ReaderState(ReaderStatus.IDLE, None)
            return AqiRead(pmtwofive=round(mean(pm25_reads), 2), pmten=round(mean(pm10_reads), 2))
        except Exception as e:
            self.state = ReaderState(ReaderStatus.ERRORING, e)
            self.reader.sleep()
            raise e

    def get_state(self) -> ReaderState:
        """Get the current state of the reader."""
        return self.state
