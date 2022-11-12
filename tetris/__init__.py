"""A simple and modular library for implementing and analysing Tetris games."""

import importlib.metadata

from tetris.board import Board
from tetris.engine import Engine, EngineFactory
from tetris.game import BaseGame
from tetris.types import (
    MinoType,
    Move,
    MoveDelta,
    MoveKind,
    PartialMove,
    Piece,
    PieceType,
    PlayingStatus,
)

__version__ = importlib.metadata.version("tetris")
__all__ = (
    "BaseGame",
    "Board",
    "Engine",
    "EngineFactory",
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
