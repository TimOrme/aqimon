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
    get_all_stats,
    add_entry,
    create_tables,
    clean_old,
)
from .read import AqiRead, Reader, ReaderStatus
from .read.mock import MockReader
from .read.novapm import NovaPmReader
from . import aqi_common
from .config import Config, get_config_from_env
import logging
from functools import lru_cache

log = logging.getLogger(__name__)

app = FastAPI()

project_root = Path(__file__).parent.resolve()
static_dir = project_root / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


@lru_cache(maxsize=1)
def get_reader(conf: Config = Depends(get_config)) -> Reader:
    """Retrieve the reader class.

    Uses LRU cache to simulate a singleton.
    """
    if conf.reader_type == "MOCK":
        return MockReader()
    elif conf.reader_type == "NOVAPM":
        return NovaPmReader(
            usb_path=conf.usb_path,
            iterations=conf.sample_count_per_read,
            sleep_time=conf.usb_sleep_time_sec,
        )
    else:
        raise Exception("Invalid reader type specified")


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
    reader = get_reader(config)

    async def read_function():
        try:
            result: AqiRead = await reader.read()
            event_time = datetime.now()
            epa_aqi_pm25 = aqi_common.calculate_epa_aqi(result.pmtwofive)
            await add_entry(
                dbconn=database,
                event_time=event_time,
                epa_aqi_pm25=epa_aqi_pm25,
                raw_pm25=result.pmtwofive,
                raw_pm10=result.pmten,
            )
            await clean_old(dbconn=database, retention_minutes=config.retention_minutes)
        except Exception as e:
            log.exception("Failed to retrieve data from reader", e)

    # Note that we leverage the @repeat_every decorator here, but as a regular function call.  This allows us to
    # use a non-global config object to specify the poll frequency
    repeater = repeat_every(seconds=config.poll_frequency_sec)
    await repeater(read_function)()


def convert_all_to_view_dict(results):
    """Convert data result to dictionary for view."""
    view = [{"t": int(x[0]), "epa": x[1], "pm25": x[2], "pm10": x[3]} for x in results]
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
    all_stats = await get_all_stats(database, window_delta)
    all_json = convert_all_to_view_dict(all_stats)
    return all_json


@app.get("/api/status")
async def status(reader: Reader = Depends(get_reader)):
    """Get the system status."""
    return {
        "reader_alive": reader.get_state().status != ReaderStatus.ERRORING,
        "reader_exception": str(reader.get_state().last_exception),
    }


def start():
    """Start the server."""
    env_config = get_config_from_env()
    uvicorn.run(app, host=env_config.server_host, port=env_config.server_port)


def debug():
    """Start the server in debug mode, with hotswapping code."""
    env_config = get_config_from_env()
    uvicorn.run("aqimon.server:app", host=env_config.server_host, port=env_config.server_port, reload=True)
