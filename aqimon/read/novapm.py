"""Nova PM SDS011 Reader module.

https://www.amazon.com/SDS011-Quality-Detection-Conditioning-Monitor/dp/B07FSDMRR5
"""
from aqimon import usb
from . import AqiRead, ReaderState, ReaderStatus
import asyncio
import serial
from statistics import mean


class NovaPmReader:
    """NOVA PM SDS011 Reader."""

    def __init__(self, usb_path: str, iterations: int = 5, sleep_time: int = 60):
        """Create the device."""
        self.usb_path = usb_path
        self.iterations = iterations
        self.sleep_time = sleep_time
        self.state = ReaderState(ReaderStatus.IDLE, None)

    async def read(self) -> AqiRead:
        """Read from the device."""
        try:
            self.state = ReaderState(ReaderStatus.READING, None)
            result = await self._power_saving_read()
            self.state = ReaderState(ReaderStatus.IDLE, None)
            return result
        except Exception as e:
            self.state = ReaderState(ReaderStatus.ERRORING, e)
            raise e

    def get_state(self) -> ReaderState:
        """Get the current state of the reader."""
        return self.state

    async def _power_saving_read(self) -> AqiRead:
        try:
            await usb.turn_on_usb()
            await asyncio.sleep(5)
        except usb.UhubCtlNotInstalled:
            pass
        result = await self._averaged_read()
        try:
            await usb.turn_off_usb()
            await asyncio.sleep(5)
        except usb.UhubCtlNotInstalled:
            pass

        return AqiRead(result.pmtwofive, result.pmten)

    async def _averaged_read(self) -> AqiRead:
        pm25_reads = []
        pm10_reads = []

        for x in range(self.iterations):
            data = self._read()
            pm25_reads.append(data.pmtwofive)
            pm10_reads.append(data.pmten)
            await asyncio.sleep(self.sleep_time)

        avg_pm25 = mean(pm25_reads)
        avg_pm10 = mean(pm10_reads)

        return AqiRead(pmtwofive=avg_pm25, pmten=avg_pm10)

    def _read(self) -> AqiRead:
        ser = serial.Serial(self.usb_path)
        data = ser.read(10)
        pmtwofive = int.from_bytes(data[2:4], byteorder="little") / 10
        pmten = int.from_bytes(data[4:6], byteorder="little") / 10
        return AqiRead(pmtwofive, pmten)
