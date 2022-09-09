"""Mutable engine implementation."""


from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from tetris.engine import Engine, Gravity, Queue, RotationSystem, Scorer
from tetris.impl.gravity import InfinityGravity
from tetris.impl.queue import SevenBag
from tetris.impl.rotation import SRS
from tetris.impl.scorer import GuidelineScorer

if TYPE_CHECKING:
    from tetris import BaseGame


class CustomEngine(Engine):
    """Mutable engine implementation.

    By default, the parts are identical to `tetris.impl.presets.ModernEngine`.

    Parameters
    ----------
    gravity : Gravity, default = tetris.impl.gravity.InfinityGravity
    queue : Queue, default = tetris.impl.queue.SevenBag
    rotation_system : RotationSystem, default = tetris.impl.rotation.SRS
    scorer : Scorer, default = tetris.impl.scorer.Scorer

    Attributes
    ----------
    parts : str to engine part mapping
        The engine parts being used. This is mutable, and changes should be
        reflected when `BaseGame.reset` is called.

    Examples
    --------
    Setting a default implementation:

    >>> from tetris import BaseGame
    >>> from tetris.impl.custom import CustomEngine
    >>> BaseGame(CustomEngine, queue=Ham)  # The default `parts["queue"]` will be `Ham`.

    Mutating the engine parts:

    >>> from tetris import BaseGame
    >>> from tetris.impl.custom import CustomEngine
    >>> game = BaseGame(CustomEngine)
    >>> game.engine.parts["gravity"] = Spam
    >>> game.reset()  # `game.gravity` is now `Spam`.
    """

    def __init__(
        self,
        gravity: type[Gravity] = InfinityGravity,
        queue: type[Queue] = SevenBag,
        rotation_system: type[RotationSystem] = SRS,
        scorer: type[Scorer] = GuidelineScorer,
    ):
        self.parts = {
            "gravity": gravity,
            "queue": queue,
            "rotation_system": rotation_system,
            "scorer": scorer,
        }

    def _get_types(
        self,
    ) -> tuple[type[Gravity], type[Queue], type[RotationSystem], type[Scorer]]:
        return (
            self.parts["gravity"],
            self.parts["queue"],
            self.parts["rotation_system"],
            self.parts["scorer"],
        )

    def gravity(self, game: BaseGame) -> Gravity:  # noqa: D102
        return self.parts["gravity"].from_game(game)

    def queue(self, game: BaseGame, pieces: Iterable[int]) -> Queue:  # noqa: D102
        return self.parts["queue"].from_game(game, pieces)

    def rotation_system(self, game: BaseGame) -> RotationSystem:  # noqa: D102
        return self.parts["rotation_system"].from_game(game)

    def scorer(self, game: BaseGame, score: int, level: int) -> Scorer:  # noqa: D102
        return self.parts["scorer"].from_game(game, score=score, level=level)
