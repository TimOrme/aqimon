"""Common AQI functionality.

Ranges here are ripped from public sites.
"""

from typing import List, Tuple, Optional, Dict
from enum import Enum
import dataclasses


class Pollutant(Enum):
    """Enum of possible pollutans."""

    PM_25 = 0
    PM_10 = 1


class EpaLevels(Enum):
    """Enum of EPA levels."""

    GOOD = 0
    MODERATE = 1
    UNHEALTHY_FOR_SENSITIVE = 2
    UNHEALTHY = 3
    VERY_UNHEALTHY = 4
    HAZARDOUS = 5


AQI: List[Tuple[int, int]] = [
    (0, 50),
    (51, 100),
    (101, 150),
    (151, 200),
    (201, 300),
    (301, 500),
]
PM_25: List[Tuple[float, float]] = [
    (0.0, 12.0),
    (12.1, 35.4),
    (35.5, 55.4),
    (55.5, 150.4),
    (150.5, 250.4),
    (250.5, 350.4),
    (350.5, 500.4),
]

PM_10: List[Tuple[float, float]] = [
    (0, 54),
    (55, 154),
    (155, 254),
    (255, 354),
    (355, 424),
    (425, 504),
    (505, 604),
]

AQI_LOOKUP_MAP: Dict[Pollutant, List[Tuple[float, float]]] = {Pollutant.PM_25: PM_25, Pollutant.PM_10: PM_10}


@dataclasses.dataclass(frozen=True)
class PollutantReading:
    """A reading for a given pollutant."""

    reading: float
    pollutant: Pollutant


@dataclasses.dataclass(frozen=True)
class EpaAqi:
    """An EPA AQI value, with the pollutant responsible for the value."""

    reading: float
    responsible_pollutant: Pollutant


def get_epa_level(epa_reading: float) -> EpaLevels:
    """Get the EPA level from a PM25 reading."""
    for i, pair in enumerate(AQI):
        if pair[0] <= epa_reading <= pair[1]:
            return EpaLevels(i)
    raise ValueError("Invalid PM value")


def calculate_epa_aqi(readings: List[PollutantReading]) -> Optional[EpaAqi]:
    """Calculate the EPA AQI from a list of pollutant readings.

    The worst possible value will be reported.
    """
    max_value: Optional[EpaAqi] = None
    for reading in readings:
        epa_value = calculate_epa_aqi_raw(reading)
        if max_value is None or max_value.reading < epa_value:
            max_value = EpaAqi(epa_value, reading.pollutant)
    return max_value


def calculate_epa_aqi_raw(pollutant_reading: PollutantReading) -> int:
    """Calculate the EPA AQI based on a pollutant reading."""
    ranges = AQI_LOOKUP_MAP[pollutant_reading.pollutant]
    for i, pm_range in enumerate(ranges):
        if pm_range[0] <= pollutant_reading.reading <= pm_range[1]:
            aqi_low = AQI[i][0]
            aqi_high = AQI[i][1]
            pm_low = pm_range[0]
            pm_high = pm_range[1]
            epa = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pollutant_reading.reading - pm_low) + aqi_low
            return round(epa)
    return -1
