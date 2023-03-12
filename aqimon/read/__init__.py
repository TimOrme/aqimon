from typing import Protocol, Optional
from dataclasses import dataclass
from enum import Enum


class ReaderStatus(Enum):
    IDLE = 1
    READING = 2
    ERRORING = 3


@dataclass(frozen=True)
class ReaderState:
    status: ReaderStatus
    last_exception: Optional[Exception]


@dataclass(frozen=True)
class AqiRead:
    pmtwofive: float
    pmten: float


class Reader(Protocol):
    async def read(self) -> AqiRead:
        pass

    def get_state(self) -> ReaderState:
        pass
