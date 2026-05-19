import operator
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class Vector(list, Generic[T]):
    def _apply_op(
        self, other: "Vector[T] | T", op: Callable, reverse: bool = False
    ) -> "Vector[T]":
        if isinstance(other, list):
            if len(self) != len(other):
                raise ValueError(
                    "Vectors must be of the same length for element-wise operations."
                )

            if reverse:
                return Vector(op(b, a) for a, b in zip(self, other))
            return Vector(op(a, b) for a, b in zip(self, other))

        else:  # Scalar operation
            if reverse:
                return Vector(op(other, a) for a in self)
            return Vector(op(a, other) for a in self)

    def _apply_iop(self, other: "Vector[T] | T", op: Callable) -> "Vector[T]":
        result = self._apply_op(other, op)
        self[:] = result  # Update the list contents in-place
        return self

    def __add__(self, other):
        return self._apply_op(other, operator.add)

    def __radd__(self, other):
        return self._apply_op(other, operator.add, reverse=True)

    def __iadd__(self, other):
        return self._apply_iop(other, operator.add)

    def __sub__(self, other):
        return self._apply_op(other, operator.sub)

    def __rsub__(self, other):
        return self._apply_op(other, operator.sub, reverse=True)

    def __isub__(self, other):
        return self._apply_iop(other, operator.sub)

    def __mul__(self, other):
        return self._apply_op(other, operator.mul)

    def __rmul__(self, other):
        return self._apply_op(other, operator.mul, reverse=True)

    def __imul__(self, other):
        return self._apply_iop(other, operator.mul)

    def __truediv__(self, other):
        return self._apply_op(other, operator.truediv)

    def __rtruediv__(self, other):
        return self._apply_op(other, operator.truediv, reverse=True)

    def __itruediv__(self, other):
        return self._apply_iop(other, operator.truediv)

    def __floordiv__(self, other):
        return self._apply_op(other, operator.floordiv)

    def __rfloordiv__(self, other):
        return self._apply_op(other, operator.floordiv, reverse=True)

    def __ifloordiv__(self, other):
        return self._apply_iop(other, operator.floordiv)

    def __mod__(self, other):
        return self._apply_op(other, operator.mod)

    def __rmod__(self, other):
        return self._apply_op(other, operator.mod, reverse=True)

    def __imod__(self, other):
        return self._apply_iop(other, operator.mod)

    def __pow__(self, other):
        return self._apply_op(other, operator.pow)

    def __rpow__(self, other):
        return self._apply_op(other, operator.pow, reverse=True)

    def __ipow__(self, other):
        return self._apply_iop(other, operator.pow)

    def __eq__(self, other):
        return self._apply_op(other, operator.eq)

    def __ne__(self, other):
        return self._apply_op(other, operator.ne)

    def __lt__(self, other):
        return self._apply_op(other, operator.lt)

    def __le__(self, other):
        return self._apply_op(other, operator.le)

    def __gt__(self, other):
        return self._apply_op(other, operator.gt)

    def __ge__(self, other):
        return self._apply_op(other, operator.ge)

    def __neg__(self) -> "Vector[T]":
        return Vector(-a for a in self)

    def __pos__(self) -> "Vector[T]":
        return Vector(+a for a in self)

    def __abs__(self) -> "Vector[T]":
        return Vector(abs(a) for a in self)

    def __invert__(self) -> "Vector[T]":
        return Vector(~a for a in self)

    def as_string(self) -> "Vector[str]":
        return Vector(str(a) for a in self)

    def as_bool(self) -> "Vector[bool]":
        return Vector(bool(a) for a in self)
