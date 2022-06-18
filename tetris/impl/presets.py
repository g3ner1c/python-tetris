"""Collection of presets from various Tetris games."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tetris.engine import Engine

if TYPE_CHECKING:
    from tetris import BaseGame

from collections.abc import Iterable

from tetris.impl import gravity
from tetris.impl import queue
from tetris.impl import rotation
from tetris.impl import scorer


class ModernEngine(Engine):
    """Modern guideline-compliant engine implementation."""

    def queue(
        self, game: BaseGame, pieces: Iterable[int]
    ) -> queue.SevenBag:  # noqa: D102
        return queue.SevenBag(pieces=pieces, seed=game.seed)

    def scorer(
        self, game: BaseGame, score: int, level: int
    ) -> scorer.GuidelineScorer:  # noqa: D102
        return scorer.GuidelineScorer(score=score, level=level)

    def rotation_system(self, game: BaseGame) -> rotation.SRS:  # noqa: D102
        return rotation.SRS(board=game.board)

    def gravity(self, game: BaseGame) -> gravity.InfinityGravity:  # noqa: D102
        return gravity.InfinityGravity(game=game)
