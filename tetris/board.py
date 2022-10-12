"""2-dimensional array object implementation."""

# TODO: a very nice long comment explaining how this magic works

from __future__ import annotations

import array
import math
import warnings
from typing import Optional, Union

from tetris.types import MinoType, PieceType

_BAD_INDEX_TYPE = "board indices must be integers, slices or tuples of integers, not {}"
_OUT_OF_BOUNDS = "board index {} out of bounds for axis {}"
_BAD_VALUE_TYPE = "board values must be integers"


class Board:
    """2-dimensional array object."""

    __slots__ = (
        "_shape",
        "_ndim",
        "_offset",
        "_strides",
        "_base",
        "_data",
        "__array_interface__",
    )

    # TODO: make a user-friendly initializer (accepting initial data) and hide
    #       the current stuff behind a private method (also completely disallow
    #       1d boards from it)

    def __init__(
        self,
        shape: tuple[int, ...],
        offset: int = 0,
        strides: Optional[tuple[int, ...]] = None,
        *,
        _base: Optional[Board] = None,
    ):
        if not 0 < len(shape) <= 2:
            raise ValueError("shape must contain 1 or 2 items")

        if strides is not None and len(strides) != len(shape):
            raise ValueError("amount of strides must match shape length")

        if _base is None and len(shape) == 1:
            warnings.warn(
                "1-dimensional board was instanced directly",
                RuntimeWarning,
                stacklevel=2,
            )

        self._shape = shape
        self._ndim = len(shape)
        self._offset = offset
        if strides is None:
            # incorrect for >=3d
            self._strides = shape[1:] + (1,)
        else:
            self._strides = strides
        self._base = _base
        if _base is not None:
            if _base._base is not None:
                self._base = _base._base
            self._data: array.array = _base._data
        else:
            self._data = array.array("B", bytes(math.prod(shape)))
            self._base = None

        # allows seamless integration with numpy
        # https://numpy.org/doc/1.23/reference/arrays.interface.html#python-side
        self.__array_interface__ = {
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
    def base(self) -> Optional[Board]:
        """The board storing the actual data, if it is not this one.

        When indexing the array, no data is copied, instead, a view onto the
        original data is created. This attribute contains the original board
        if this board is a view.
        """
        return self._base

    # TODO: is `_offset` and `_strides` of any interest to be public? and is
    #       `_data` useful too, if `tobytes` exists?

    def tobytes(self) -> bytes:
        """Return a copy of this board as a bytes object.

        Currently this can only return the data in C-style (row-major) order.

        Returns
        -------
        bytes
        """
        return self._data[
            self._offset : self._offset
            + self._strides[0] * self._shape[0] : self._strides[0]
        ].tobytes()

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

        raise TypeError(_BAD_INDEX_TYPE.format(type(k).__name__))

    def _contiguous_blocks(self, key: slice):
        """Yield largest contiguous blocks for a given slice."""
        start, stop, step = key.indices(self._shape[0])
        stride = self._strides[0] * step
        offset = self._offset + start * self._strides[0]
        length = stride * max(math.ceil((stop - start) / step), 0)
        if self._ndim == 1:
            yield (offset, offset + length, stride)
        else:
            for i in range(offset, offset + length, stride):
                yield (i, i + self._strides[1] * self._shape[1], self._strides[1])

    def __getitem__(self, key: Union[int, slice, tuple[int, int]]) -> Union[Board, int]:
        # TODO: tuples with slices? might be unnecessary

        key = self._normalize_index(key)

        if isinstance(key, int):
            if self._ndim == 1:
                return self._data[self._offset + key * self._strides[0]]

            return Board(
                (self._shape[1],),
                self._offset + key * self._strides[0],
                (self._strides[1],),
                _base=self,
            )

        if isinstance(key, slice):
            start, stop, step = key.indices(self._shape[0])

            return Board(
                (max(math.ceil((stop - start) / step), 0), *self._shape[1:]),
                self._offset + start * self._strides[0],
                (self._strides[0] * step, *self._strides[1:]),
                _base=self,
            )

        if isinstance(key, tuple):
            a, b = key
            return self._data[
                self._offset + a * self._strides[0] + b * self._strides[1]
            ]

    def __setitem__(
        self, key: Union[int, slice, tuple[int, int]], value: Union[Board, int]
    ) -> None:
        key = self._normalize_index(key)

        if isinstance(key, int):
            if hasattr(value, "__len__"):
                if self._ndim == 1:
                    raise TypeError("can't assign sequence to element index")
                raise NotImplementedError  # TODO
            else:
                if not hasattr(value, "__index__"):
                    raise TypeError(_BAD_VALUE_TYPE)
                offset = self._offset + key * self._strides[0]
                if self._ndim == 1:
                    self._data[offset] = int(value)  # type: ignore[arg-type]
                else:
                    for i in range(offset, offset + self._shape[1], self._strides[1]):
                        self._data[i] = int(value)  # type: ignore[arg-type]

        elif isinstance(key, slice):
            if hasattr(value, "__len__"):
                raise NotImplementedError  # TODO
            else:
                if not hasattr(value, "__index__"):
                    raise TypeError(_BAD_VALUE_TYPE)

                for start, stop, step in self._contiguous_blocks(key):
                    for i in range(start, stop, step):
                        self._data[i] = int(value)  # type: ignore[arg-type]

        elif isinstance(key, tuple):
            a, b = key
            if not hasattr(value, "__index__"):
                raise TypeError(_BAD_VALUE_TYPE)

            self._data[
                self._offset + a * self._strides[0] + b * self._strides[1]
            ] = int(
                value  # type: ignore[arg-type]
            )

    def __iter__(self):
        start = self._offset
        stop = self._offset + self._strides[0] * self._shape[0]
        stride = self._strides[0]
        if self._ndim == 1:
            yield from self._data[start:stop:stride]
        else:
            for i in range(start, stop, stride):
                yield Board((self._shape[1],), i, (self._strides[1],), _base=self)

    def __len__(self):
        return self._shape[0]

    def __repr__(self) -> str:
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
                    text += tiles.get(i) or PieceType(i).name
                    text += " "
                text += "\n"

        text = text.lstrip(" ")
        text = text.rstrip("\n")
        return f"<Board [{text}])>"
