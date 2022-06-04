"""Collection of gravity implementations."""

from __future__ import annotations

import time
from typing import Final, Optional, TYPE_CHECKING

from tetris.engine import Gravity
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind

if TYPE_CHECKING:
    from tetris import BaseGame

SECOND: Final[int] = 1_000_000_000  # in nanoseconds


class Timer:
    """Helper class for time-keeping.

    Parameters
    ----------
    seconds : default = 0
    milliseconds : default = 0
    microseconds : default = 0
    nanoseconds : default = 0
    """

    __slots__ = ("duration", "running", "started")

    def __init__(
        self,
        *,
        seconds: float = 0,
        milliseconds: float = 0,
        microseconds: float = 0,
        nanoseconds: float = 0,
    ):
        self.duration = int(
            seconds * 1e9 + milliseconds * 1e6 + microseconds * 1e3 + nanoseconds
        )
        self.started = 0
        self.running = False

    def start(self) -> None:
        """(re)start the timer."""
        self.started = time.monotonic_ns()
        self.running = True

    def stop(self) -> None:
        """Stop the timer."""
        self.started = 0
        self.running = False

    @property
    def done(self) -> bool:
        """True if this timer is running and has finished."""
        return self.running and self.started + self.duration <= time.monotonic_ns()


class InfinityGravity(Gravity):
    """Marathon gravity with Infinity lock delay.

    Notes
    -----
    See <https://tetris.wiki/Infinity> and <https://tetris.wiki/Marathon>.
    """

    def __init__(self, game: BaseGame):
        self.game = game

        self.idle_lock = Timer(milliseconds=500)
        self.lock_resets = 0
        self.last_drop = time.monotonic_ns()

    def calculate(self, delta: Optional[MoveDelta] = None) -> None:  # noqa: D102
        level = self.game.level
        piece = self.game.piece
        drop_delay = (0.8 - ((level - 1) * 0.007)) ** (level - 1) * SECOND
        now = time.monotonic_ns()

        if delta is not None:
            if delta.kind == MoveKind.hard_drop:
                self.idle_lock.stop()
                self.lock_resets = 0

            if self.idle_lock.running and (delta.x or delta.y or delta.r):
                self.idle_lock.start()
                self.lock_resets += 1

            if not self.idle_lock.running and self.game.rs.overlaps(
                minos=piece.minos, px=piece.x + 1, py=piece.y
            ):
                self.idle_lock.start()

        if self.idle_lock.done or self.lock_resets >= 15:
            self.game.push(Move(kind=MoveKind.hard_drop, auto=True))
            self.idle_lock.stop()
            self.lock_resets = 0

        since_drop = now - self.last_drop
        if since_drop >= drop_delay:
            self.game.push(
                Move(kind=MoveKind.soft_drop, x=int(since_drop / drop_delay), auto=True)
            )
            self.last_drop = now
            if not self.idle_lock.running and self.game.rs.overlaps(
                minos=piece.minos, px=piece.x + 1, py=piece.y
            ):
                self.idle_lock.start()
