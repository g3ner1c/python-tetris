from __future__ import annotations

import array
import math
import warnings
from typing import Optional, Union


class Board:
    __slots__ = (
        "_shape",
        "_size",
        "_ndim",
        "_offset",
        "_strides",
        "_base",
        "_data",
        "__array_interface__",
    )

    def __init__(
        self,
        shape: tuple[int, int] | tuple[int] | int,
        offset: int = 0,
        strides: Optional[tuple[int, int] | tuple[int]] = None,
        *,
        _base: Optional[Board] = None,
    ):
        if isinstance(shape, int):
            shape = (shape,)

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

        if strides is None:
            # incorrect for >=3d
            strides = shape[1:] + (1,)

        self._shape = shape
        self._size = math.prod(shape)
        self._ndim = len(shape)
        self._offset = offset
        self._strides = strides
        self._base = _base
        if _base is not None:
            if _base._base is not None:
                self._base = _base._base
            self._data = _base._data
        else:
            self._data = array.array("B", bytes(self._size))
            self._base = None

        # allows seamless integration with numpy
        # https://numpy.org/doc/1.23/reference/arrays.interface.html#python-side
        self.__array_interface__ = {
            "data": self._data,
            "offset": offset,
            "shape": shape,
            "strides": strides,
            "typestr": "|u1",
            "version": 3,
        }

    def tobytes(self) -> bytes:
        return self._data.tobytes()

    def __getitem__(
        self, key: Union[int, slice, tuple[Union[int, slice], ...]]
    ) -> Union[Board, int]:
        if isinstance(key, tuple):
            if len(key) > self._ndim:
                raise IndexError(f"too many indices for {self._ndim}d board")
            if len(key) == 1:
                key = key[0]

        if isinstance(key, int):
            if key < 0:
                key += self._shape[0]
            if not 0 <= key < self._shape[0]:
                raise IndexError("board index out of range")

            if self._ndim == 1:
                return self._data[self._offset + key * self._strides[0]]

            return Board(
                (self._shape[1],),
                self._offset + key * self._strides[0],
                (self._strides[1],),
                _base=self,
            )

        if isinstance(key, slice):
            ...

        if isinstance(key, tuple):
            ...

    def __iter__(self):
        if self._ndim == 1:
            yield from self._data[
                self._offset : self._offset + self._shape[0] : self._strides[0]
            ]
        else:
            for i in range(
                self._offset, self._strides[0] * self._shape[0], self._strides[0]
            ):
                yield Board(
                    (self._shape[1],),
                    i,
                    (self._strides[1],),
                    _base=self,
                )

    def __len__(self):
        return self._shape[0]
