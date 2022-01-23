from __future__ import annotations

import time
from typing import Final, Optional, TYPE_CHECKING

from tetris.engine.abcs import Gravity
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind

if TYPE_CHECKING:
    from tetris import BaseGame

SECOND: Final[int] = 1_000_000_000  # in nanoseconds


class MarathonGravity(Gravity):
    def __init__(self, game: BaseGame):
        self.game = game

        now = time.monotonic_ns()
        self.last_input = now
        self.last_drop = now
        self.last_hdrop = now + 1

    def calculate(self, delta: Optional[MoveDelta] = None):
        level = self.game.level
        drop_delay = (0.8 - ((level - 1) * 0.007)) ** (level - 1) * SECOND
        now = time.monotonic_ns()

        if delta is not None and delta.kind == MoveKind.hard_drop:
            self.last_hdrop = now

        if now - self.last_hdrop >= 30 * SECOND:
            self.game.push(Move(kind=MoveKind.hard_drop, auto=True))
            self.last_hdrop = now

        since_drop = now - self.last_drop
        if since_drop >= drop_delay:
            self.game.push(
                Move(kind=MoveKind.soft_drop, x=int(since_drop / drop_delay), auto=True)
            )
            self.last_drop = now
