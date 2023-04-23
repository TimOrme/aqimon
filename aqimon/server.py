"""Core server module."""
from fastapi import FastAPI, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
from starlette.responses import FileResponse
import uvicorn
import databases
from pathlib import Path
from datetime import datetime, timedelta
from .database import (
    get_all_reads,
    get_all_epa_aqis,
    add_read,
    add_epa_read,
    get_averaged_reads,
    create_tables,
    clean_old,
    ReadLogEntry,
    EpaAqiLogEntry,
)
from .read import AqiRead, Reader
from .read.mock import MockReader
from .read.novapm import OpinionatedReader
from . import aqi_common
from .config import Config, get_config_from_env
import logging
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional, List

log = logging.getLogger(__name__)

app = FastAPI()

project_root = Path(__file__).parent.resolve()
static_dir = project_root / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

POLLUTANT_MAP = {aqi_common.Pollutant.PM_10: "PM10", aqi_common.Pollutant.PM_25: "PM25"}


@dataclass
class ScheduledReader:
    """Simple state wrapper to track reader, and next schedule time."""

    next_schedule: Optional[datetime]
    reader: Reader


@lru_cache(maxsize=1)
def get_config():
    """Retrieve config from environment.

    Uses LRU cache to simulate a singleton.
    """
    return get_config_from_env()


@lru_cache(maxsize=1)
def get_database(config: Config = Depends(get_config)) -> databases.Database:
    """Retrieve database instance.

    Creates a path to the database if it doesn't exist.

    Uses LRU cache to simulate a singleton.
    """
    Path(config.database_path).parent.mkdir(parents=True, exist_ok=True)
    return databases.Database(f"sqlite+aiosqlite:///{config.database_path}")


def build_reader() -> ScheduledReader:
    """Retrieve the reader class.

    Uses LRU cache to simulate a singleton.
    """
    conf = get_config()
    if conf.reader_type == "MOCK":
        return ScheduledReader(None, MockReader())
    elif conf.reader_type == "NOVAPM":
        return ScheduledReader(
            None,
            OpinionatedReader(
                ser_dev=conf.usb_path,
                warm_up_secs=conf.warm_up_sec,
                iterations=conf.sample_count_per_read,
                sleep_time=conf.sleep_sec_between_reads,
                command_wait_time=conf.command_wait_time,
            ),
        )
    else:
        raise Exception("Invalid reader type specified")


reader = build_reader()


def get_reader() -> ScheduledReader:
    """Retrieve the global reader to find state from.

    TODO: Change this to not rely on global module-level state.
    """
    global reader
    return reader


@app.on_event("startup")
async def database_connect():
    """Connect to the database, and create tables on startup."""
    database = get_database(get_config_from_env())
    await database.connect()
    await create_tables(database)


@app.on_event("shutdown")
async def database_disconnect():
    """Disconnect from the database on shutdown."""
    database = get_database(get_config_from_env())
    await database.disconnect()


@app.on_event("startup")
async def read_from_device() -> None:
    """Background cron task to read from the device."""
    config = get_config_from_env()
    database = get_database(config)
    scheduled_reader = get_reader()

    async def read_function() -> None:
        try:
            # Set the approximate time of the next read
            result: AqiRead = await scheduled_reader.reader.read()
            event_time = datetime.now()
            await add_read(
                dbconn=database,
                event_time=event_time,
                pm25=result.pmtwofive,
                pm10=result.pmten,
            )

            averaged_reads = await get_averaged_reads(
                dbconn=database, lookback_to=event_time - timedelta(minutes=config.epa_lookback_minutes)
            )
            if averaged_reads:
                read_list = [
                    aqi_common.PollutantReading(averaged_reads.avg_pm25, aqi_common.Pollutant.PM_25),
                    aqi_common.PollutantReading(averaged_reads.avg_pm10, aqi_common.Pollutant.PM_10),
                ]
                epa_aqi = aqi_common.calculate_epa_aqi(read_list)

                if epa_aqi:
                    pollutant = POLLUTANT_MAP.get(epa_aqi.responsible_pollutant)

                    if pollutant is None:
                        raise Exception(f"Invalid Pollutant! {epa_aqi.responsible_pollutant}")

                    await add_epa_read(
                        dbconn=database,
                        event_time=event_time,
                        epa_aqi=epa_aqi.reading,
                        pollutant=pollutant,
                        read_count=averaged_reads.count,
                        oldest_read_time=averaged_reads.oldest_read_time,
                    )
                else:
                    log.warning("No EPA Value was calculated.")

            await clean_old(dbconn=database, retention_minutes=config.retention_minutes)
            scheduled_reader.next_schedule = datetime.now() + timedelta(seconds=config.poll_frequency_sec)
        except Exception as e:
            log.exception("Failed to retrieve data from reader", e)
            scheduled_reader.next_schedule = datetime.now() + timedelta(seconds=config.poll_frequency_sec)

    # Note that we leverage the @repeat_every decorator here, but as a regular function call.  This allows us to
    # use a non-global config object to specify the poll frequency
    repeater = repeat_every(seconds=config.poll_frequency_sec)
    await repeater(read_function)()


def convert_all_to_view_dict(reads: List[ReadLogEntry], epas: List[EpaAqiLogEntry]):
    """Convert data result to dictionary for view."""
    view = {
        "reads": [{"t": int(x.event_time.timestamp()), "pm25": x.pm25, "pm10": x.pm10} for x in reads],
        "epas": [{"t": int(x.event_time.timestamp()), "epa": x.epa_aqi} for x in epas],
    }
    return view


@app.get("/", response_class=HTMLResponse)
async def home():
    """Return the index page."""
    return FileResponse(static_dir / "index.html")


@app.get("/api/sensor_data")
async def all_data(
    database: databases.Database = Depends(get_database),
    window: str = "all",
):
    """Retrieve sensor data for the given window."""
    window_delta = None
    if window == "hour":
        window_delta = timedelta(hours=1)
    elif window == "day":
        window_delta = timedelta(days=1)
    elif window == "week":
        window_delta = timedelta(weeks=1)
    if window_delta:
        all_reads = await get_all_reads(database, datetime.now() - window_delta)
        all_epas = await get_all_epa_aqis(database, datetime.now() - window_delta)
    else:
        all_reads = await get_all_reads(database, None)
        all_epas = await get_all_epa_aqis(database, None)
    all_json = convert_all_to_view_dict(all_reads, all_epas)
    return all_json


@app.get("/api/status")
async def status(reader: ScheduledReader = Depends(get_reader)):
    """Get the system status."""
    last_exception = reader.reader.get_state().last_exception

    return {
        "reader_status": str(reader.reader.get_state().status.name),
        "reader_exception": str(last_exception) if last_exception else None,
        "next_schedule": int(reader.next_schedule.timestamp() * 1000) if reader.next_schedule else None,
    }


def start():
    """Start the server."""
    env_config = get_config_from_env()
    uvicorn.run(app, host=env_config.server_host, port=env_config.server_port)


def debug():
    """Start the server in debug mode, with hotswapping code."""
    env_config = get_config_from_env()
    uvicorn.run("aqimon.server:app", host=env_config.server_host, port=env_config.server_port, reload=True)
