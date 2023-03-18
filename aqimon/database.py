"""Database operations."""
from datetime import datetime, timedelta
from typing import Optional
import databases


async def get_latest_stats(dbconn: databases.Database):
    """Get the most recent read from the database."""
    result = await dbconn.fetch_one("SELECT * FROM aqi_log ORDER BY event_time DESC LIMIT 1")
    if result:
        return result[0], result[1], result[2], result[3]
    else:
        return 0, 0, 0, 0


async def get_all_stats(dbconn: databases.Database, window_delta: Optional[timedelta]):
    """Retrieve all read stats, for a given time window.

    If no window is specified, all results are returned.
    """
    if window_delta:
        lookback = int((datetime.now() - window_delta).timestamp())
        return await dbconn.fetch_all(
            "SELECT * FROM aqi_log WHERE event_time >= :lookback ORDER BY event_time ASC",
            values={"lookback": lookback},
        )
    else:
        return await dbconn.fetch_all("SELECT * FROM aqi_log ORDER BY event_time ASC")


async def clean_old(dbconn: databases.Database, retention_minutes: int):
    """Remove expired database entries.

    This is used to keep the database from going infinitely, and allows us to define a retention period.
    """
    last_week = datetime.now() - timedelta(minutes=retention_minutes)
    last_week_timestamp = int(last_week.timestamp())
    await dbconn.execute(
        "DELETE FROM aqi_log WHERE event_time < :last_week_timestamp",
        values={"last_week_timestamp": last_week_timestamp},
    )


async def add_entry(dbconn: databases.Database, event_time, epa_aqi_pm25, raw_pm25, raw_pm10):
    """Add a read entry to the database."""
    formatted_time = int(event_time.timestamp())
    await dbconn.execute(
        query="INSERT INTO aqi_log VALUES (:formatted_time, :epa_aqi_pm25, :raw_pm25, :raw_pm10)",
        values={
            "formatted_time": formatted_time,
            "epa_aqi_pm25": epa_aqi_pm25,
            "raw_pm25": raw_pm25,
            "raw_pm10": raw_pm10,
        },
    )


async def create_tables(dbconn: databases.Database):
    """Create database tables, if they don't already exist."""
    await dbconn.execute(
        """CREATE TABLE IF NOT EXISTS aqi_log (event_time integer, epa_aqi_pm25 real, raw_pm25 real, raw_pm10 real)"""
    )
    await dbconn.execute("""CREATE INDEX IF NOT EXISTS aqi_eventtime ON aqi_log (event_time)""")
