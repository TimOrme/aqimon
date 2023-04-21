"""Reader module."""
from typing import Protocol, Optional
from dataclasses import dataclass
from enum import Enum


class ReaderStatus(Enum):
    """Enum of possible reader states."""

    IDLE = 1
    WARM_UP = 2
    READING = 3
    ERRORING = 4


@dataclass(frozen=True)
class ReaderState:
    """State of a reader.

    Used to report status and errors to the user.
    """

    status: ReaderStatus
    last_exception: Optional[Exception]


@dataclass(frozen=True)
class AqiRead:
    """A raw read from an AQI device."""

    pmtwofive: float
    pmten: float


class Reader(Protocol):
    """Protocol for a reader.

    Hypothetically could be implemented for any number of devices.
    """

    async def read(self) -> AqiRead:
        """Read from the device."""
        pass

    def get_state(self) -> ReaderState:
        """Get the state of the reader."""
        pass
