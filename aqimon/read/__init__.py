from typing import Protocol, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class AqiRead:
    pmtwofive: float
    pmten: float


class Reader(Protocol):
    def read(self) -> AqiRead:
        pass


@dataclass(frozen=True)
class ReaderState:
    alive: bool
    last_exception: Optional[Exception]
