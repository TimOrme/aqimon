import random
import asyncio
from aqimon.read import AqiRead, ReaderState, ReaderStatus


class MockReader:
    def __init__(self, fake_sleep_secs=5):
        self.state = ReaderState(ReaderStatus.IDLE, None)
        self.fake_sleep_secs = fake_sleep_secs

    async def read(self) -> AqiRead:
        self.state = ReaderState(ReaderStatus.READING, None)
        pm25: float = round(random.uniform(0.0, 500.4), 2)
        pm10: float = round(random.uniform(0.0, 300.0), 2)
        result = AqiRead(pmtwofive=pm25, pmten=pm10)
        await asyncio.sleep(self.fake_sleep_secs)
        self.state = ReaderState(ReaderStatus.IDLE, None)
        return result

    def get_state(self) -> ReaderState:
        return self.state
