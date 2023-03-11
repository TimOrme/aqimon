import os.path
from typing import Optional
from dataclasses import dataclass
from serde import serde
from serde.toml import to_toml, from_toml

DEFAULT_CONFIG_PATH = "~/.aqimon/config"
DEFAULT_DB_PATH = "~/.aqimon/db.sqlite"


@serde
@dataclass(frozen=True)
class Config:
    database_path: str
    poll_frequency_sec: int
    retention_minutes: int

    reader_type: str

    # Nova PM properties
    usb_path: str
    usb_sleep_time_sec: int
    sample_count_per_read: int


DEFAULT_CONFIG = Config(
    database_path=os.path.expanduser(DEFAULT_DB_PATH),
    poll_frequency_sec=60 * 15,  # Every 15 minutes
    retention_minutes=60 * 24 * 7,  # 1 week
    reader_type="NOVAPM",
    usb_path="/dev/ttyUSB0",
    usb_sleep_time_sec=5,
    sample_count_per_read=5,
)


def _load_config(path: str) -> Config:
    with open(path, "r") as file:
        return from_toml(Config, file.read())


def save_config(config: Config, path: str):
    with open(path, "w") as file:
        file.write(to_toml(config))


def get_config(passed_config_path: Optional[str]) -> Config:
    if passed_config_path and os.path.exists(passed_config_path):
        return _load_config(passed_config_path)
    elif not passed_config_path and os.path.exists(DEFAULT_CONFIG_PATH):
        return _load_config(DEFAULT_CONFIG_PATH)
    else:
        return DEFAULT_CONFIG
