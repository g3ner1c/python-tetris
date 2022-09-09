"""Collection of presets from various Tetris games."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tetris.engine import Engine

if TYPE_CHECKING:
    from tetris import BaseGame

from collections.abc import Iterable

from tetris.impl import gravity, queue, rotation, scorer


class ModernEngine(Engine):
    """Modern guideline-compliant engine implementation."""

    def _get_types(
        self,
    ) -> tuple[
        type[gravity.InfinityGravity],
        type[queue.SevenBag],
        type[rotation.SRS],
        type[scorer.GuidelineScorer],
    ]:  # noqa: D102
        return (
            gravity.InfinityGravity,
            queue.SevenBag,
            rotation.SRS,
            scorer.GuidelineScorer,
        )

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


class TetrioEngine(ModernEngine):
    """TETR.IO-specific engine implementation."""

    def _get_types(
        self,
    ) -> tuple[
        type[gravity.InfinityGravity],
        type[queue.SevenBag],
        type[rotation.TetrioSRS],
        type[scorer.GuidelineScorer],
    ]:  # noqa: D102
        return (
            gravity.InfinityGravity,
            queue.SevenBag,
            rotation.TetrioSRS,
            scorer.GuidelineScorer,
        )

    def rotation_system(self, game: BaseGame) -> rotation.TetrioSRS:  # noqa: D102
        return rotation.TetrioSRS(board=game.board)


class NESEngine(Engine):
    """1989 Nintendo NES Tetris engine implementation."""

    def _get_types(
        self,
    ) -> tuple[
        type[gravity.NESGravity],
        type[queue.NES],
        type[rotation.NRS],
        type[scorer.NESScorer],
    ]:  # noqa: D102
        return (gravity.NESGravity, queue.NES, rotation.NRS, scorer.NESScorer)

    def queue(self, game: BaseGame, pieces: Iterable[int]) -> queue.NES:  # noqa: D102
        return queue.NES(pieces=pieces, seed=game.seed)

    def scorer(
        self, game: BaseGame, score: int, level: int
    ) -> scorer.NESScorer:  # noqa: D102
        return scorer.NESScorer(
            score=score, level=level, initial_level=game.rules.initial_level
        )

    def rotation_system(self, game: BaseGame) -> rotation.NRS:  # noqa: D102
        return rotation.NRS(board=game.board)

    def gravity(self, game: BaseGame) -> gravity.NESGravity:  # noqa: D102
        return gravity.NESGravity(game=game)
