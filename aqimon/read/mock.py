"""Mock reader class.

Useful for testing locally, when you don't have a real reader available.
"""
import random
import asyncio
from aqimon.read import AqiRead, ReaderState, ReaderStatus


class MockReader:
    """Mock reader class."""

    def __init__(self, fake_sleep_secs=5):
        """Create a mock reader."""
        self.state = ReaderState(ReaderStatus.IDLE, None)
        self.fake_sleep_secs = fake_sleep_secs

    async def read(self) -> AqiRead:
        """Read from the 'device'.

        Returns randomized data for the mock class.
        """
        self.state = ReaderState(ReaderStatus.READING, None)
        pm25: float = round(random.uniform(0.0, 500.4), 2)
        pm10: float = round(random.uniform(0.0, 300.0), 2)
        result = AqiRead(pmtwofive=pm25, pmten=pm10)
        await asyncio.sleep(self.fake_sleep_secs)
        self.state = ReaderState(ReaderStatus.IDLE, None)
        return result

    def get_state(self) -> ReaderState:
        """Get the state of the reader."""
        return self.state
