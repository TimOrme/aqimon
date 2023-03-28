"""Mock reader class.

Useful for testing locally, when you don't have a real reader available.
"""
import random
import asyncio
import logging
from aqimon.read import AqiRead, ReaderState, ReaderStatus


class MockReader:
    """Mock reader class."""

    def __init__(self, fake_sleep_secs=5, raise_error_odds=50):
        """Create a mock reader."""
        self.state = ReaderState(ReaderStatus.IDLE, None)
        self.fake_sleep_secs = fake_sleep_secs
        self.raise_error_odds = raise_error_odds

    async def read(self) -> AqiRead:
        """Read from the 'device'.

        Returns randomized data for the mock class.

        Also, randomly fails some percentage of the time.
        """
        try:
            self.state = ReaderState(ReaderStatus.READING, None)
            raise_error_roll = random.randint(0, 100)
            if raise_error_roll < self.raise_error_odds:
                raise Exception("Fake error from the reader.")
            pm25: float = round(random.uniform(0.0, 500.4), 2)
            pm10: float = round(random.uniform(0.0, 300.0), 2)
            result = AqiRead(pmtwofive=pm25, pmten=pm10)

            await asyncio.sleep(self.fake_sleep_secs)
            self.state = ReaderState(ReaderStatus.IDLE, None)
            return result
        except Exception as e:
            self.state = ReaderState(ReaderStatus.ERRORING, e)
            raise e

    def get_state(self) -> ReaderState:
        """Get the state of the reader."""
        logging.info(self.state)
        return self.state
