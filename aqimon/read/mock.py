import random
from aqimon.read import AqiRead


class MockReader:
    async def read(self) -> AqiRead:
        pm25: float = round(random.uniform(0.0, 500.4), 2)
        pm10: float = round(random.uniform(0.0, 300.0), 2)
        return AqiRead(pmtwofive=pm25, pmten=pm10)
