"""Config module."""
import os.path
from dataclasses import dataclass

DEFAULT_DB_PATH = "~/.aqimon/db.sqlite"


@dataclass(frozen=True)
class Config:
    """Config data for the application."""

    database_path: str
    poll_frequency_sec: int
    retention_minutes: int

    reader_type: str

    # Nova PM properties
    usb_path: str
    sleep_sec_between_reads: int
    sample_count_per_read: int
    warm_up_sec: int
    command_wait_time: int

    # EPA Properties
    epa_lookback_minutes: int

    # Server properties
    server_port: int
    server_host: str


DEFAULT_CONFIG = Config(
    database_path=os.path.expanduser(DEFAULT_DB_PATH),
    poll_frequency_sec=60 * 15,  # Every 15 minutes
    retention_minutes=60 * 24 * 7,  # 1 week
    epa_lookback_minutes=60 * 8,  # 8 hours
    reader_type="NOVAPM",
    usb_path="/dev/ttyUSB0",
    sleep_sec_between_reads=5,
    warm_up_sec=15,
    command_wait_time=1,
    sample_count_per_read=5,
    server_port=8000,
    server_host="0.0.0.0",
)


def get_config_from_env() -> Config:
    """Get the config from environment variables."""
    return Config(
        database_path=os.path.expanduser(os.environ.get("AQIMON_DB_PATH", DEFAULT_CONFIG.database_path)),
        poll_frequency_sec=int(os.environ.get("AQIMON_POLL_FREQUENCY_SEC", DEFAULT_CONFIG.poll_frequency_sec)),
        retention_minutes=int(os.environ.get("AQIMON_RETENTION_MINUTES", DEFAULT_CONFIG.retention_minutes)),
        reader_type=os.environ.get("AQIMON_READER_TYPE", DEFAULT_CONFIG.reader_type),
        usb_path=os.environ.get("AQIMON_USB_PATH", DEFAULT_CONFIG.usb_path),
        sleep_sec_between_reads=int(
            os.environ.get("AQIMON_SLEEP_SEC_BETWEEN_READS", DEFAULT_CONFIG.sleep_sec_between_reads)
        ),
        warm_up_sec=int(os.environ.get("AQIMON_WARM_UP_SEC", DEFAULT_CONFIG.warm_up_sec)),
        command_wait_time=int(os.environ.get("AQIMON_COMMAND_WAIT_TIME", DEFAULT_CONFIG.command_wait_time)),
        sample_count_per_read=int(os.environ.get("AQIMON_SAMPLE_COUNT_PER_READ", DEFAULT_CONFIG.sample_count_per_read)),
        server_port=int(os.environ.get("AQIMON_SERVER_PORT", DEFAULT_CONFIG.server_port)),
        server_host=os.environ.get("AQIMON_SERVER_HOST", DEFAULT_CONFIG.server_host),
        epa_lookback_minutes=int(os.environ.get("AQIMON_EPA_LOOKBACK_MIN", DEFAULT_CONFIG.epa_lookback_minutes)),
    )
