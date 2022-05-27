"""Mutable engine implementation."""


from __future__ import annotations

from typing import TYPE_CHECKING

from tetris.engine import Engine
from tetris.engine import Gravity
from tetris.engine import Queue
from tetris.engine import RotationSystem
from tetris.engine import Scorer
from tetris.impl import modern

if TYPE_CHECKING:
    from tetris import BaseGame


class CustomEngine(Engine):
    """Mutable engine implementation.

    By default, the parts are taken from `tetris.impl.modern`.

    Parameters
    ----------
    gravity : Gravity, default = tetris.impl.modern.InfinityGravity
    queue : Queue, default = tetris.impl.modern.SevenBag
    rotation_system : RotationSystem, default = tetris.impl.modern.SRS
    scorer : Scorer, default = tetris.impl.modern.Scorer

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
        gravity: Gravity = modern.InfinityGravity,
        queue: Queue = modern.SevenBag,
        rotation_system: RotationSystem = modern.SRS,
        scorer: Scorer = modern.Scorer,
    ):
        self.parts = {
            "gravity": gravity,
            "queue": queue,
            "rotation_system": rotation_system,
            "scorer": scorer,
        }

    def gravity(self, game: BaseGame) -> Gravity:  # noqa: D102
        return self.parts["gravity"].from_game(game)

    def queue(self, game: BaseGame) -> Queue:  # noqa: D102
        return self.parts["queue"].from_game(game)

    def rotation_system(self, game: BaseGame) -> RotationSystem:  # noqa: D102
        return self.parts["rotation_system"].from_game(game)

    def scorer(self, game: BaseGame) -> Scorer:  # noqa: D102
        return self.parts["scorer"].from_game(game)
