"""A simple and modular library for implementing and analysing Tetris games."""

import importlib.metadata

from tetris import engine, game, impl, types
from tetris.engine import Engine
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
    "engine",
    "Engine",
    "game",
    "impl",
    "MinoType",
    "Move",
    "MoveDelta",
    "MoveKind",
    "PartialMove",
    "Piece",
    "PieceType",
    "PlayingStatus",
    "types",
)

del importlib
