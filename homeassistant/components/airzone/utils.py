"""Const for Airzone."""
from enum import Enum


class ZoneMode(Enum):
    """Const with modes."""

    MANUAL = 0
    MANUAL_SLEEP = 1
    AUTOMATIC = 2
    AUTOMATIC_SLEEP = 3


class FancoilSpeed(Enum):
    """Const with fan speed."""

    AUTOMATIC = 0
    SPEED_1 = 1
    SPEED_2 = 2
    SPEED_3 = 3
