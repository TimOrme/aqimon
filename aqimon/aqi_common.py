"""Common AQI functionality.

Ranges here are ripped from public sites.
"""

from typing import List, Tuple

AQI: List[Tuple[int, int]] = [
    (0, 50),
    (51, 100),
    (101, 150),
    (151, 200),
    (201, 300),
    (301, 400),
    (401, 500),
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


def get_level_from_pm25(pm25: float) -> int:
    """Get the EPA level from a PM25 reading."""
    for i, pair in enumerate(PM_25):
        if pair[0] <= pm25 <= pair[1]:
            return i
    raise ValueError("Invalid PM value")


def calculate_epa_aqi(pm_25_read: float) -> int:
    """Calculate the EPA AQI based on a PM25 reading."""
    for i, pm_range in enumerate(PM_25):
        if pm_range[0] <= pm_25_read <= pm_range[1]:
            aqi_low = AQI[i][0]
            aqi_high = AQI[i][1]
            pm_low = pm_range[0]
            pm_high = pm_range[1]
            epa = ((aqi_high - aqi_low) / (pm_high - pm_low)) * (pm_25_read - pm_low) + aqi_low
            return round(epa)
    return -1
