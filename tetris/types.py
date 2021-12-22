import enum
from collections.abc import Sequence
from typing import Union

import numpy as np
from numpy.typing import NDArray

PieceType = enum.IntEnum("PieceType", "I L J S Z T O")
Board = NDArray[np.int8]
KickTable = dict[PieceType, dict[tuple[int, int], tuple[tuple[int, int], ...]]]
Minos = tuple[tuple[int, int], ...]
Seed = Union[str, bytes, int]
QueueSeq = Sequence[PieceType]
