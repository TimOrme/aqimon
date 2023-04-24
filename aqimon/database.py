"""Database operations."""
from datetime import datetime, timedelta
from typing import Optional, List
import databases
from dataclasses import dataclass


@dataclass(frozen=True)
class AveragedRead:
    """An averaged read result.

    Includes the number of reads that went into the average, as well as the oldest timestamp of those reads.
    """

    avg_pm25: float
    avg_pm10: float
    count: int
    oldest_read_time: datetime


@dataclass(frozen=True)
class ReadLogEntry:
    """A read log entry."""

    event_time: datetime
    pm25: float
    pm10: float


@dataclass(frozen=True)
class EpaAqiLogEntry:
    """An EPA Aqi log entry."""

    event_time: datetime
    epa_aqi: float
    pollutant: str
    read_count: int
    oldest_read_time: datetime


async def get_latest_read(dbconn: databases.Database) -> ReadLogEntry:
    """Get the most recent read from the database."""
    result = await dbconn.fetch_one("SELECT event_time, pm25, pm10 FROM read_log ORDER BY event_time DESC LIMIT 1")
    if result:
        return ReadLogEntry(datetime.fromtimestamp(result[0]), result[1], result[2])
    else:
        return ReadLogEntry(datetime.now(), 0, 0)


async def get_latest_epa_aqi(dbconn: databases.Database) -> EpaAqiLogEntry:
    """Get the most recent EPA AQI from the database."""
    result = await dbconn.fetch_one(
        "SELECT event_time, epa_aqi, pollutant, read_count, oldest_read_time "
        "FROM epa_aqi_log ORDER BY event_time DESC LIMIT 1"
    )
    if result:
        return EpaAqiLogEntry(
            event_time=datetime.fromtimestamp(result[0]),
            epa_aqi=result[1],
            pollutant=result[2],
            read_count=result[3],
            oldest_read_time=datetime.fromtimestamp(result[4]),
        )
    else:
        return EpaAqiLogEntry(
            event_time=datetime.now(), epa_aqi=0, pollutant="NA", read_count=0, oldest_read_time=datetime.now()
        )


async def get_all_reads(dbconn: databases.Database, lookback: Optional[datetime]) -> List[ReadLogEntry]:
    """Retrieve all read stats, for a given time window.

    If no window is specified, all results are returned.
    """
    if lookback:
        data = await dbconn.fetch_all(
            "SELECT event_time, pm10, pm25 FROM read_log WHERE event_time >= :lookback ORDER BY event_time ASC",
            values={"lookback": int(lookback.timestamp())},
        )
    else:
        data = await dbconn.fetch_all("SELECT event_time, pm10, pm25 FROM read_log ORDER BY event_time ASC")

    return [ReadLogEntry(event_time=datetime.fromtimestamp(x[0]), pm10=x[1], pm25=x[2]) for x in data]


async def get_all_epa_aqis(dbconn: databases.Database, lookback: Optional[datetime]) -> List[EpaAqiLogEntry]:
    """Retrieve all read stats, for a given time window.

    If no window is specified, all results are returned.
    """
    if lookback:
        data = await dbconn.fetch_all(
            "SELECT event_time, epa_aqi, pollutant, read_count, oldest_read_time "
            "FROM epa_aqi_log "
            "WHERE event_time >= :lookback ORDER BY event_time ASC",
            values={"lookback": int(lookback.timestamp())},
        )
    else:
        data = await dbconn.fetch_all(
            "SELECT event_time, epa_aqi, pollutant, read_count, oldest_read_time "
            "FROM epa_aqi_log ORDER BY event_time ASC"
        )

    return [
        EpaAqiLogEntry(
            event_time=datetime.fromtimestamp(x[0]),
            epa_aqi=x[1],
            pollutant=x[2],
            read_count=x[3],
            oldest_read_time=datetime.fromtimestamp(x[4]),
        )
        for x in data
    ]


async def get_averaged_reads(dbconn: databases.Database, lookback_to: datetime) -> Optional[AveragedRead]:
    """Get the average read values, looking back to a certain time.

    Note that the lookback will include one additional value outside of the window if it exists.  This allows for us to
    ensure full coverage of the lookback window.
    """
    lookback = int(lookback_to.timestamp())
    result = await dbconn.fetch_one(
        "SELECT "
        "ROUND(AVG(pm25), 2) as avg_pm25, ROUND(AVG(pm10), 2) as avg_pm10, "
        "COUNT(*) as count, "
        "MIN(event_time) as oldest_time "
        "FROM read_log "
        "WHERE (event_time >= :lookback) OR "
        "(event_time = (SELECT MAX(event_time) FROM read_log WHERE event_time <= :lookback)) ORDER BY event_time ASC",
        values={"lookback": lookback},
    )

    if result is None:
        return None
    else:
        return AveragedRead(
            avg_pm25=result[0],
            avg_pm10=result[1],
            count=result[2],
            oldest_read_time=datetime.fromtimestamp(result[3]),
        )


async def clean_old(dbconn: databases.Database, retention_minutes: int) -> None:
    """Remove expired database entries.

    This is used to keep the database from going infinitely, and allows us to define a retention period.
    """
    last_week = datetime.now() - timedelta(minutes=retention_minutes)
    last_week_timestamp = int(last_week.timestamp())
    await dbconn.execute(
        "DELETE FROM read_log WHERE event_time < :last_week_timestamp",
        values={"last_week_timestamp": last_week_timestamp},
    )


async def add_epa_read(
    dbconn: databases.Database,
    event_time: datetime,
    epa_aqi: float,
    pollutant: str,
    read_count: int,
    oldest_read_time: datetime,
):
    """Add an EPA read entry to the database."""
    formatted_time = int(event_time.timestamp())
    formatted_oldest_read_time = int(oldest_read_time.timestamp())
    await dbconn.execute(
        query="INSERT INTO epa_aqi_log VALUES (:formatted_time, :epa_aqi, :pollutant, :read_count, :oldest_read_time)",
        values={
            "formatted_time": formatted_time,
            "epa_aqi": epa_aqi,
            "pollutant": pollutant,
            "read_count": read_count,
            "oldest_read_time": formatted_oldest_read_time,
        },
    )


async def add_read(dbconn: databases.Database, event_time: datetime, pm25: float, pm10: float):
    """Add a raw read entry to the database."""
    formatted_time = int(event_time.timestamp())
    await dbconn.execute(
        query="INSERT INTO read_log VALUES (:formatted_time, :pm25, :pm10)",
        values={
            "formatted_time": formatted_time,
            "pm25": pm25,
            "pm10": pm10,
        },
    )


async def create_tables(dbconn: databases.Database):
    """Create database tables, if they don't already exist."""
    await dbconn.execute("""CREATE TABLE IF NOT EXISTS read_log (event_time integer, pm25 real, pm10 real)""")
    await dbconn.execute("""CREATE INDEX IF NOT EXISTS read_eventtime ON read_log (event_time)""")
    await dbconn.execute(
        """CREATE TABLE IF NOT EXISTS epa_aqi_log 
        (event_time integer, epa_aqi real, pollutant text, read_count integer, oldest_read_time integer)"""
    )
    await dbconn.execute("""CREATE INDEX IF NOT EXISTS eqpaqi_eventtime ON epa_aqi_log (event_time)""")
