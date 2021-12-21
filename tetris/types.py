import enum
from typing import Iterable, Union

import numpy as np
from numpy.typing import NDArray

PieceType = enum.IntEnum("PieceType", "I L J S Z T O")
Board = NDArray[np.int8]
Minos = tuple[tuple[int, int], ...]
Seed = Union[str, bytes, int]
QueueSeq = Iterable[PieceType]
