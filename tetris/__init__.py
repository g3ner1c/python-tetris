"""A simple and modular library for implementing and analysing Tetris games."""

import importlib.metadata

from tetris.engine import Engine
from tetris.game import BaseGame
from tetris.types import MinoType
from tetris.types import Move
from tetris.types import MoveDelta
from tetris.types import MoveKind
from tetris.types import PartialMove
from tetris.types import Piece
from tetris.types import PieceType
from tetris.types import PlayingStatus

__version__ = importlib.metadata.version("tetris")
__all__ = (
    "BaseGame",
    "Engine",
    "MinoType",
    "Move",
    "MoveDelta",
    "MoveKind",
    "PartialMove",
    "Piece",
    "PieceType",
    "PlayingStatus",
)

del importlib
