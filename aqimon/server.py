import json
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_utils.tasks import repeat_every
import uvicorn
import databases
from pathlib import Path
from datetime import datetime
from .database import (
    get_latest_stats,
    get_all_stats,
    add_entry,
    create_tables,
    clean_old,
)
from .read import AqiRead, Reader, ReaderState
from .read.mock import MockReader
from .read.novapm import NovaPmReader
from . import aqi_common
from .config import Config, get_config

app = FastAPI()
config = get_config(None)


project_root = Path(__file__).parent.resolve()

static_dir = project_root / "static"
template_dir = project_root / "templates"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

Path(config.database_path).parent.mkdir(parents=True, exist_ok=True)
database = databases.Database(f"sqlite+aiosqlite:///{config.database_path}")
templates = Jinja2Templates(directory=template_dir)


def _get_reader(conf: Config) -> Reader:
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


reader = _get_reader(config)
reader_state = ReaderState(False, None)


@app.on_event("startup")
async def database_connect():
    await database.connect()
    await create_tables(database)


@app.on_event("startup")
@repeat_every(seconds=5)
async def read_from_device() -> None:
    global reader_state
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
        reader_state = ReaderState(True, None)
    except Exception as e:
        reader_state = ReaderState(False, e)


@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()


def convert_all_to_view_dict(results):
    view = {}
    view["t"] = []
    view["epa"] = []
    view["pm25"] = []
    view["pm10"] = []
    for x in results:
        view["t"].append(datetime.fromtimestamp(int(x[0])).strftime("%m-%d %H:%M"))
        view["epa"].append(x[1])
        view["pm25"].append(x[2])
        view["pm10"].append(x[3])
    return view


@app.post("/add")
async def add_new_entry() -> AqiRead:
    data = await reader.read()
    epa_aqi_pm25 = aqi_common.calculate_epa_aqi(data.pmtwofive)
    await add_entry(
        dbconn=database,
        event_time=datetime.now(),
        epa_aqi_pm25=epa_aqi_pm25,
        raw_pm25=data.pmtwofive,
        raw_pm10=data.pmten,
    )
    return data


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.get("/api/alldata")
async def all_data():
    all_stats = await get_all_stats(database)
    all_json = convert_all_to_view_dict(all_stats)
    return all_json


@app.get("/api/status")
async def status():
    return {
        "reader_alive": reader_state.alive,
        "reader_exception": str(reader_state.last_exception)
        if reader_state is not None
        else None,
    }


def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)
