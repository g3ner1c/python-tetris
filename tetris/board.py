"""2-dimensional array object implementation."""

from __future__ import annotations

import array
import math
import sys
from collections.abc import Iterable, Iterator, Sequence
from typing import TYPE_CHECKING, Any, Optional, SupportsIndex, Union, cast, overload

from tetris.types import BoardLike, MinoType, PieceType, _SupportsArray

__all__ = ("Board",)

_BAD_INDEX_TYPE = "board indices must be integers, slices or tuples of integers, not {}"
_OUT_OF_BOUNDS = "board index {} out of bounds for axis {}"
_BAD_VALUE_TYPE = "board values must be integers"
_BAD_BROADCAST = "can't broadcast board from shape {} into {}"
_WRONG_DIMENSIONS = "boards can only have 1 or 2 dimensions"
_BAD_AXIS_LENGTH = "board axis {} must have non-zero length"
_INHOMOGENEOUS_SEQ = "the given sequence is not homogeneous. can't create board"
_BAD_RESHAPE = "can't reshape {} into {}"


def _broadcast(board: Any, shape: tuple[int, ...]) -> Board:
    if not isinstance(board, Board):
        board = Board(board)

    if board._ndim > len(shape):
        raise ValueError(_BAD_BROADCAST.format(board._shape, shape))

    if board._ndim == len(shape):
        if board._shape != shape:
            raise ValueError(_BAD_BROADCAST.format(board._shape, shape))
        # same shapes, no broadcasting
        return cast(Board, board).copy()

    if board._shape[0] != shape[1]:
        raise ValueError(_BAD_BROADCAST.format(board._shape, shape))

    # repeat data across first axis: (y) -> (x, y)
    return Board([[*board.data]] * shape[0])


def _reshape(old_shape: tuple[int, ...], new_shape: tuple[int, ...]) -> tuple[int, ...]:
    old_prod = math.prod(old_shape)

    unknown_dim = None
    for i, j in enumerate(new_shape):
        if j < 0:
            if unknown_dim is not None:
                raise ValueError("can't specify two unknown dimensions")
            unknown_dim = i

    if unknown_dim is not None:
        fixed_shape = list(new_shape)
        fixed_shape[unknown_dim] = 1
        new_axis = old_prod / math.prod(fixed_shape)
        if new_axis % 1 != 0:
            raise ValueError(_BAD_RESHAPE.format(old_shape, new_shape))
        fixed_shape[unknown_dim] = int(new_axis)
        return tuple(fixed_shape)

    if math.prod(old_shape) != math.prod(new_shape):
        raise ValueError(_BAD_RESHAPE.format(old_shape, new_shape))

    return new_shape


# XXX: `typing.Protocol` instance checks are considerably slower than just
#      checking the required method, so some unusual assertions are made as
#      mypy does not recognise that


class Board:
    r"""2-dimensional homogeneous array containing minos.

    Parameters
    ----------
    obj : board_like
        A board, any (nested) sequence, or an object whose ``__array__`` method
        returns a `np.ndarray`.
    shape : tuple of ints, optional
        If provided, the object will be reshaped into this. One of the axes can
        be negative, in which it's value will be inferred from the remaining
        axes. (e.g.: (-1, 8) for a sequence with 16 elements will use (2, 8))

    Attributes
    ----------
    shape : tuple of ints
        The board's shape.
    ndim : int
        The board's number of dimensions.
    strides : tuple of ints
        The board's strides for each axis.
    base : Board
        If the board is a view, this is the board containing the actual data.
    data : array.array
        The board's raw data in memory.

    Examples
    --------
    Creating a board:

    >>> from tetris import Board
    >>> Board([[0, 0, 0, 0], [0, 0, 0, 0]])
    <Board [. . . .
            . . . .]>
    >>> Board.zeros((5, 4))
    <Board [. . . .
            . . . .
            . . . .
            . . . .
            . . . .]
    >>> Board.frombuffer(b"\0\0\3\4\3\0\0", (3,), offset=2)
    <Board [L O L ])>

    Indexing:

    >>> b = Board([*range(8)] * 20, (16, 10))
    >>> b[1]
    <Board [J L O S T Z . I J L ])>
    >>> b[::4]
    <Board [. I J L O S T Z . I
            . I J L O S T Z . I
            . I J L O S T Z . I
            . I J L O S T Z . I ])>
    >>> b[1, 2]
    4
    """

    # https://github.com/python/mypy/issues/1021
    _shape: tuple[int, ...]
    _ndim: int
    _offset: int
    _strides: tuple[int, ...]
    _base: Optional[Board]
    _data: array.array[int]

    __slots__ = (
        "_shape",
        "_ndim",
        "_offset",
        "_strides",
        "_base",
        "_data",
    )

    def __new__(cls, obj: BoardLike, shape: Optional[tuple[int, ...]] = None) -> Board:
        """Create and return a new board object."""
        if shape is not None and not 0 < len(shape) <= 2:
            raise ValueError(_WRONG_DIMENSIONS)

        if isinstance(obj, Board):
            b = obj.copy()
            if shape is not None:
                shape = _reshape(b._shape, shape)
                b._shape = shape
                b._ndim = len(shape)
                b._strides = shape[1:] + (1,)
            return b

        if hasattr(obj, "__array__") and "numpy" in sys.modules:
            if TYPE_CHECKING:
                assert isinstance(obj, _SupportsArray)
            import numpy as np

            arr = obj.__array__(np.int8)
            if isinstance(arr, np.ndarray):
                if shape is not None:
                    arr.shape = shape
                if not 0 < arr.ndim <= 2:
                    raise ValueError(_WRONG_DIMENSIONS)
                self = object.__new__(cls)
                self._shape = arr.shape
                self._ndim = arr.ndim
                self._offset = 0
                self._strides = arr.strides
                self._base = None
                self._data = array.array("B", arr.data.tobytes())
                return self

        if hasattr(obj, "__len__"):
            if TYPE_CHECKING:
                assert not isinstance(obj, _SupportsArray)
            s_shape: tuple[int, ...] = (len(obj),)
            if s_shape[0] == 0:
                raise ValueError(_BAD_AXIS_LENGTH.format(0))

            data = array.array("B")

            if hasattr(obj[0], "__len__"):
                if TYPE_CHECKING:
                    obj = cast(Sequence[Sequence[SupportsIndex]], obj)
                # nested sequence - 2d array
                s_shape = (len(obj), len(obj[0]))
                if s_shape[1] == 0:
                    raise ValueError(_BAD_AXIS_LENGTH.format(1))
                if hasattr(obj[0][0], "__len__"):
                    # double nested - 3d
                    raise ValueError(_WRONG_DIMENSIONS)
                data = array.array("B")
                for ln in obj:
                    if not hasattr(ln, "__len__") or len(ln) != s_shape[1]:
                        raise ValueError(_INHOMOGENEOUS_SEQ)
                    for i in ln:
                        if hasattr(i, "__len__"):
                            raise ValueError(_INHOMOGENEOUS_SEQ)
                        data.append(int(i))
            else:
                if TYPE_CHECKING:
                    obj = cast(Sequence[SupportsIndex], obj)
                # not nested - 1d
                data = array.array("B")
                for i in obj:
                    if hasattr(i, "__len__"):
                        raise ValueError(_INHOMOGENEOUS_SEQ)
                    data.append(int(i))

            self = object.__new__(cls)
            if shape is not None:
                self._shape = _reshape(s_shape, shape)
            else:
                self._shape = s_shape

            self._ndim = len(self._shape)
            self._strides = self._shape[1:] + (1,)
            self._offset = 0
            self._base = None
            self._data = data
            return self

        raise TypeError(f"can't convert {obj} into {cls.__name__}")

    @classmethod
    def zeros(cls, shape: tuple[int, ...]) -> Board:
        """Create a new board initialised with zeros.

        Parameters
        ----------
        shape : tuple of ints
            The board's shape. must have 1 or 2 non-zero values.
        """
        if not 0 < len(shape) <= 2:
            raise ValueError(_WRONG_DIMENSIONS)
        for i, x in enumerate(shape):
            if x < 0:
                raise ValueError(_BAD_AXIS_LENGTH.format(i))
        self = object.__new__(cls)
        self._shape = shape
        self._ndim = len(shape)
        self._offset = 0
        # incorrect for >=3d
        self._strides = shape[1:] + (1,)
        self._base = None
        self._data = array.array("B", bytes(math.prod(shape)))
        return self

    @classmethod
    def frombuffer(
        cls,
        buffer: Union[array.array[int], Iterable[int]],
        shape: tuple[int, ...],
        offset: int = 0,
        strides: Optional[tuple[int, ...]] = None,
    ) -> Board:
        """Create a new board using existing data.

        Parameters
        ----------
        buffer : bytes-like object
            Data to use. If already an `array.array`, no data is copied.
        shape : tuple of ints
        offset : int, optional
        strides : tuple of ints, optional
        """
        if not isinstance(buffer, array.array):
            buffer = array.array("B", buffer)
        if not 0 < len(shape) <= 2:
            raise ValueError(_WRONG_DIMENSIONS)
        if offset < 0 or len(buffer) - offset < math.prod(shape):
            raise ValueError("shape is out of bounds to buffer")
        if strides is not None and len(strides) != len(shape):
            raise ValueError("strides count must be same amount as dimensions")

        self = object.__new__(cls)
        self._shape = shape
        self._ndim = len(shape)
        self._offset = offset
        if strides is None:
            strides = shape[1:] + (1,)
        self._strides = strides
        self._base = None
        self._data = buffer
        return self

    @classmethod
    def _view(
        cls,
        base: Board,
        shape: tuple[int, ...],
        offset: int,
        strides: tuple[int, ...],
    ) -> Board:
        self = object.__new__(cls)
        self._shape = shape
        self._ndim = len(shape)
        self._offset = offset
        self._strides = strides
        self._base = base
        if base._base is not None:
            self._base = base._base
        self._data = base._data
        return self

    # allows seamless integration with numpy
    # https://numpy.org/doc/1.23/reference/arrays.interface.html#python-side

    @property
    def __array_interface__(self) -> dict[str, Any]:
        return {
            "data": self._data,
            "offset": self._offset,
            "shape": self._shape,
            "strides": self._strides,
            "typestr": "|u1",
            "version": 3,
        }

    @property
    def shape(self) -> tuple[int, ...]:
        """The board's shape."""
        return self._shape

    @property
    def ndim(self) -> int:
        """The board's number of dimensions."""
        return self._ndim

    @property
    def strides(self) -> tuple[int, ...]:
        """The spacing between successive elements in memory for each axis."""
        return self._strides

    @property
    def base(self) -> Optional[Board]:
        """The board storing the actual data, if it is not this one.

        When indexing the array, no data is copied, instead, a view onto the
        original data is created. This attribute contains the original board
        if this board is a view.
        """
        return self._base

    @property
    def data(self) -> array.array[int]:
        """The board's raw data, as an `array.array`.

        This is always a copy. For views, this only contains the elements it
        has access to.
        """
        start = self._offset
        stop = self._offset + self._strides[0] * self._shape[0]
        stride = self._strides[0]
        if self._ndim == 1:
            return self._data[start:stop:stride]
        arr = array.array("B")
        for i in range(start, stop, stride):
            arr += self._data[
                i :
                i + self._strides[1] * self._shape[1] :
                self._strides[1]
            ]  # fmt: skip
        return arr

    def tobytes(self) -> bytes:
        """Return a copy of this board as a bytes object.

        Currently this can only return the data in C-style (row-major) order.

        Returns
        -------
        bytes
        """
        return self.data.tobytes()

    def copy(self) -> Board:
        """Return a copy of this board as another board."""
        new = object.__new__(Board)
        new._shape = self._shape
        new._ndim = self._ndim
        new._offset = 0
        new._strides = self._shape[1:] + (1,)
        new._base = None
        new._data = self.data
        return new

    def _normalize_index(
        self, key: Union[int, slice, tuple[int, int]]
    ) -> Union[int, slice, tuple[int, int]]:
        """Apply various checks and convert things like negative indices."""
        if hasattr(key, "__index__"):
            k = int(key)  # type: ignore[arg-type]
            if k < 0:
                k += self._shape[0]
            if not 0 <= k < self._shape[0]:
                raise IndexError(_OUT_OF_BOUNDS.format(key, 0))
            return k

        if isinstance(key, slice):
            # nothing to be done really
            return key

        if isinstance(key, tuple):
            if self._ndim != 2 or len(key) != 2:
                raise ValueError("can only index 2d arrays with 2-tuples")
            a, b = key
            if not hasattr(a, "__index__") or not hasattr(b, "__index__"):
                raise TypeError(
                    _BAD_INDEX_TYPE.format(f"({type(a).__name__}, {type(b).__name__})")
                )
            a, b = int(a), int(b)
            if a < 0:
                a += self._shape[0]
            if not 0 <= a < self._shape[0]:
                raise IndexError(_OUT_OF_BOUNDS.format(key[0], 0))
            if b < 0:
                b += self._shape[1]
            if not 0 <= b < self._shape[1]:
                raise IndexError(_OUT_OF_BOUNDS.format(key[1], 1))
            return a, b

        raise TypeError(_BAD_INDEX_TYPE.format(type(key).__name__))

    def _contiguous_blocks(self, key: slice) -> Iterator[tuple[int, int, int]]:
        """Yield largest contiguous blocks for a given slice."""
        start, stop, step = key.indices(self._shape[0])
        stride = self._strides[0] * step
        offset = self._offset + start * self._strides[0]
        length = stride * max(math.ceil((stop - start) / step), 0)
        # only a single row
        if self._ndim == 1:
            yield (offset, offset + length, stride)
            return
        # evenly spaced rows
        if self._strides[1] * self._shape[1] == stride:
            yield (offset, offset + length, self._strides[1])
            return
        # worst case - all rows are incontiguous (e.g. when slicing as [::2])
        for i in range(offset, offset + length, stride):
            yield (i, i + self._strides[1] * self._shape[1], self._strides[1])

    @overload
    def __getitem__(self, key: slice) -> Board:
        ...

    @overload
    def __getitem__(self, key: tuple[int, int]) -> int:
        ...

    @overload
    def __getitem__(self, key: int) -> Union[Board, int]:
        ...

    def __getitem__(self, key: Union[int, slice, tuple[int, int]]) -> Union[Board, int]:
        key = self._normalize_index(key)

        if isinstance(key, int):
            if self._ndim == 1:
                return self._data[self._offset + key * self._strides[0]]

            return Board._view(
                self,
                (self._shape[1],),
                self._offset + key * self._strides[0],
                (self._strides[1],),
            )

        if isinstance(key, slice):
            start, stop, step = key.indices(self._shape[0])

            return Board._view(
                self,
                (max(math.ceil((stop - start) / step), 0), *self._shape[1:]),
                self._offset + start * self._strides[0],
                (self._strides[0] * step, *self._strides[1:]),
            )

        a, b = key
        return self._data[self._offset + a * self._strides[0] + b * self._strides[1]]

    def __setitem__(
        self, key: Union[int, slice, tuple[int, int]], value: Union[Board, int]
    ) -> None:
        key = self._normalize_index(key)

        if isinstance(key, int):
            offset = self._offset + key * self._strides[0]
            if hasattr(value, "__len__"):
                if self._ndim == 1:
                    raise TypeError("can't assign sequence to element index")
                length = self._shape[1]
                stride = self._strides[1]
                arr = _broadcast(value, (self._shape[1],))
                self._data[offset : offset + length : stride] = arr.data
            else:
                if not hasattr(value, "__index__"):
                    raise TypeError(_BAD_VALUE_TYPE)
                if self._ndim == 1:
                    self._data[offset] = int(value)
                else:
                    length = self._shape[1]
                    stride = self._strides[1]
                    for i in range(offset, offset + length, stride):
                        self._data[i] = int(value)

        elif isinstance(key, slice):
            if hasattr(value, "__len__"):
                arr = _broadcast(value, self[key]._shape)
                if arr._base is not None:
                    arr = arr.copy()  # FIXME: can this be done without copying?
                x = 0
                for start, stop, step in self._contiguous_blocks(key):
                    length = len(self._data[start:stop:step])
                    self._data[start:stop:step] = arr._data[x : x + length]
                    x += length
            else:
                if not hasattr(value, "__index__"):
                    raise TypeError(_BAD_VALUE_TYPE)

                for start, stop, step in self._contiguous_blocks(key):
                    for i in range(start, stop, step):
                        self._data[i] = int(value)

        else:
            a, b = key
            if not hasattr(value, "__index__"):
                raise TypeError(_BAD_VALUE_TYPE)

            self._data[
                self._offset + a * self._strides[0] + b * self._strides[1]
            ] = int(value)

    def __iter__(self) -> Iterator[Any]:
        start = self._offset
        stop = self._offset + self._strides[0] * self._shape[0]
        stride = self._strides[0]
        if self._ndim == 1:
            yield from self._data[start:stop:stride]
        else:
            for i in range(start, stop, stride):
                yield Board._view(self, (self._shape[1],), i, (self._strides[1],))

    def __len__(self) -> int:
        return self._shape[0]

    def __repr__(self) -> str:
        max_i = max(MinoType)
        tiles = {
            MinoType.EMPTY: ".",
            MinoType.GHOST: "@",
            MinoType.GARBAGE: "X",
        }
        text = ""

        if self._ndim == 1:
            for i in self:
                text += tiles.get(i) or PieceType(i).name
                text += " "
        else:
            for line in self:
                text += "        "
                for i in line:
                    if i > max_i:
                        text += "? "
                        continue
                    text += tiles.get(i) or PieceType(i).name
                    text += " "
                text += "\n"

        text = text.lstrip(" ")
        text = text.rstrip("\n")
        return f"<Board [{text}])>"
