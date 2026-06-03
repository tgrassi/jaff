"""
Unit registry, conversions, and the :class:`Quantity` value object.

This module centralizes the unit-conversion factors that were previously
scattered as magic numbers throughout JAFF.  Every factor is sourced from
:mod:`jaff.physics.constants` (the ``cgs`` set) so there is a single source of
truth and no duplicated literals.

Two layers are provided:

- A registry (:data:`_UNITS`) plus the :func:`convert` function.  Within a
  physical dimension a conversion is a pure multiplicative ratio to that
  dimension's CGS base unit.  Conversions *between* dimensions
  (wavelength/frequency/temperature <-> energy) go through a small set of
  physics **bridges** because, e.g., ``E = h c / lambda`` is inverse in the
  wavelength and therefore cannot be expressed as a constant factor.
- The :class:`Quantity` class, a lightweight ``(value, unit)`` pair supporting
  ``.to()``, attribute-style access (``q.eV``), and same-dimension arithmetic.

All conversions are numpy-elementwise: ``value`` may be a float or an
:class:`numpy.ndarray`.

Examples
--------
>>> from jaff.physics import units
>>> units.convert(13.605693, "eV", "Ry")
1.0
>>> units.convert(121.567, "nm", "eV")  # Lyman-alpha  # doctest: +ELLIPSIS
10.19...
>>> units.Quantity(121.6, "nm").eV  # doctest: +ELLIPSIS
10.1...
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import overload

import numpy as np

from ..errors import IncompatibleUnitsError, UnknownUnitError
from ._typing import Numeric
from .constants import cgs

# Accepted input: any Numeric, plus python sequences coerced to float arrays.
ArrayLike = Numeric | list | tuple


def _coerce(value: ArrayLike) -> Numeric:
    """Turn lists/tuples into float arrays; leave scalars and arrays untouched."""
    if isinstance(value, (list, tuple)):
        return np.asarray(value, dtype=float)
    return value


class Dimension(Enum):
    """The physical dimension a unit measures."""

    ENERGY = "energy"
    LENGTH = "length"
    AREA = "area"
    TIME = "time"
    CHARGE = "charge"
    MASS = "mass"
    TEMPERATURE = "temperature"
    FREQUENCY = "frequency"


@dataclass(frozen=True)
class Unit:
    """
    A named unit and its multiplicative factor to the CGS base unit.

    Parameters
    ----------
    name : str
        Canonical unit symbol (e.g. ``"eV"``).
    dimension : Dimension
        Physical dimension the unit belongs to.
    factor : float
        Multiplying a value in this unit by ``factor`` yields the value in the
        dimension's CGS base unit.  The base unit therefore has ``factor == 1``.
    """

    name: str
    dimension: Dimension
    factor: float


@dataclass(frozen=True)
class Bridge:
    """
    A physics link between two dimensions, acting on CGS base values.

    ``forward`` maps a value in ``src``'s base unit to ``dst``'s base unit;
    ``backward`` is its inverse.  Both must be numpy-elementwise.

    Parameters
    ----------
    src, dst : Dimension
        The two dimensions the bridge connects.
    forward, backward : Callable[[Numeric], Numeric]
        Inverse maps between the CGS base units of ``src`` and ``dst``.
    """

    src: Dimension
    dst: Dimension
    forward: Callable[[Numeric], Numeric]
    backward: Callable[[Numeric], Numeric]


# Unit registry.  The base unit of each dimension has ``factor == 1``; every
# other factor is the value of one such unit expressed in the CGS base unit.
# Factors are taken from ``constants.cgs`` wherever a constant exists, so there
# are no duplicated magic numbers.
_UNITS: dict[str, Unit] = {
    # ENERGY -- base: erg
    "erg": Unit("erg", Dimension.ENERGY, 1.0),
    "eV": Unit("eV", Dimension.ENERGY, cgs.ev_to_erg),
    "keV": Unit("keV", Dimension.ENERGY, cgs.ev_to_erg * 1e3),
    "MeV": Unit("MeV", Dimension.ENERGY, cgs.ev_to_erg * 1e6),
    "J": Unit("J", Dimension.ENERGY, 1e7),
    "Ry": Unit("Ry", Dimension.ENERGY, cgs.Ry_hc),
    # LENGTH -- base: cm
    "cm": Unit("cm", Dimension.LENGTH, 1.0),
    "m": Unit("m", Dimension.LENGTH, 1e2),
    "nm": Unit("nm", Dimension.LENGTH, 1e-7),
    "angstrom": Unit("angstrom", Dimension.LENGTH, 1e-8),
    "um": Unit("um", Dimension.LENGTH, 1e-4),
    # AREA -- base: cm2
    "cm2": Unit("cm2", Dimension.AREA, 1.0),
    "m2": Unit("m2", Dimension.AREA, 1e4),
    "barn": Unit("barn", Dimension.AREA, cgs.barn),
    "Mb": Unit("Mb", Dimension.AREA, cgs.mbarn),
    # TIME -- base: s
    "s": Unit("s", Dimension.TIME, 1.0),
    "ms": Unit("ms", Dimension.TIME, 1e-3),
    "us": Unit("us", Dimension.TIME, 1e-6),
    "ns": Unit("ns", Dimension.TIME, 1e-9),
    # CHARGE -- base: esu (statC)
    "esu": Unit("esu", Dimension.CHARGE, 1.0),
    "statC": Unit("statC", Dimension.CHARGE, 1.0),
    "C": Unit("C", Dimension.CHARGE, cgs.c / 10.0),
    # MASS -- base: g
    "g": Unit("g", Dimension.MASS, 1.0),
    "kg": Unit("kg", Dimension.MASS, 1e3),
    "amu": Unit("amu", Dimension.MASS, cgs.amu),
    "m_e": Unit("m_e", Dimension.MASS, cgs.m_e),
    "m_p": Unit("m_p", Dimension.MASS, cgs.m_p),
    # TEMPERATURE -- base: K
    "K": Unit("K", Dimension.TEMPERATURE, 1.0),
    # FREQUENCY -- base: Hz
    "Hz": Unit("Hz", Dimension.FREQUENCY, 1.0),
}


# Cross-dimension bridges, keyed by the unordered pair of dimensions they join.
# Each map operates on CGS base values (erg, cm, K, Hz).
_BRIDGES: dict[frozenset[Dimension], Bridge] = {
    # wavelength (cm) <-> energy (erg):  E = h c / lambda  (self-inverse)
    frozenset({Dimension.LENGTH, Dimension.ENERGY}): Bridge(
        Dimension.LENGTH,
        Dimension.ENERGY,
        forward=lambda x: cgs.h * cgs.c / x,
        backward=lambda x: cgs.h * cgs.c / x,
    ),
    # frequency (Hz) <-> energy (erg):  E = h nu
    frozenset({Dimension.FREQUENCY, Dimension.ENERGY}): Bridge(
        Dimension.FREQUENCY,
        Dimension.ENERGY,
        forward=lambda x: cgs.h * x,
        backward=lambda x: x / cgs.h,
    ),
    # temperature (K) <-> energy (erg):  E = k_b T
    frozenset({Dimension.TEMPERATURE, Dimension.ENERGY}): Bridge(
        Dimension.TEMPERATURE,
        Dimension.ENERGY,
        forward=lambda x: cgs.k_b * x,
        backward=lambda x: x / cgs.k_b,
    ),
}


def _lookup(name: str) -> Unit:
    """Return the :class:`Unit` named ``name`` or raise :class:`UnknownUnitError`."""
    try:
        return _UNITS[name]
    except KeyError:
        raise UnknownUnitError(
            f"unknown unit {name!r}; known units: {sorted(_UNITS)}"
        ) from None


def convert(value: ArrayLike, from_unit: str, to_unit: str) -> Numeric:
    """
    Convert ``value`` from ``from_unit`` to ``to_unit``.

    Within a dimension the conversion is a pure factor ratio.  Across
    dimensions it routes through a registered physics bridge
    (wavelength/frequency/temperature <-> energy).  Works elementwise on
    floats or numpy arrays.

    Parameters
    ----------
    value : float or numpy.ndarray
        The numeric value(s) to convert.
    from_unit, to_unit : str
        Registered unit names.

    Returns
    -------
    float or numpy.ndarray
        ``value`` expressed in ``to_unit``.

    Raises
    ------
    UnknownUnitError
        If either unit name is not registered.
    IncompatibleUnitsError
        If the units' dimensions differ and no bridge connects them.

    Examples
    --------
    >>> convert(13.605693, "eV", "Ry")
    1.0
    >>> convert(1.0, "Mb", "cm2")
    1e-18
    """
    u_from = _lookup(from_unit)
    u_to = _lookup(to_unit)

    base = _coerce(value) * u_from.factor  # value in from-dimension's CGS base unit

    if u_from.dimension is not u_to.dimension:
        bridge = _BRIDGES.get(frozenset({u_from.dimension, u_to.dimension}))
        if bridge is None:
            raise IncompatibleUnitsError(
                f"cannot convert {from_unit!r} ({u_from.dimension.value}) to "
                f"{to_unit!r} ({u_to.dimension.value}): no bridge between dimensions"
            )
        if bridge.src is u_from.dimension:
            base = bridge.forward(base)
        else:
            base = bridge.backward(base)
        # base is now in the to-dimension's CGS base unit

    return base / u_to.factor


class Quantity:
    """
    A ``(value, unit)`` pair with conversion, attribute access, and arithmetic.

    Parameters
    ----------
    value : float or numpy.ndarray
        The magnitude.
    unit : str
        A registered unit name.

    Notes
    -----
    Attribute access returns the value converted to the named unit, so
    ``Quantity(1.0, "eV").erg`` yields the value in erg.  Addition and
    subtraction require operands of the same dimension; multiplication and
    division by a scalar preserve the unit; dividing two same-dimension
    quantities yields a dimensionless float.  Compound units (products of
    quantities) are out of scope.

    Examples
    --------
    >>> q = Quantity(121.6, "nm")
    >>> q.to("angstrom").value
    1216.0
    >>> (Quantity(1.0, "eV") + Quantity(1.0, "keV")).eV
    1001.0
    """

    # Declared so the type checker does not fall back to ``__getattr__``'s
    # ``Numeric`` return type for these slots.
    value: Numeric
    _unit: str

    __slots__ = ("value", "_unit")

    def __init__(self, value: ArrayLike, unit: str) -> None:
        object.__setattr__(self, "value", _coerce(value))
        object.__setattr__(self, "_unit", _lookup(unit).name)

    @property
    def unit(self) -> str:
        """The unit symbol this quantity is expressed in."""
        return self._unit

    @property
    def dimension(self) -> Dimension:
        """The physical dimension of this quantity."""
        return _UNITS[self._unit].dimension

    def to(self, unit: str) -> "Quantity":
        """Return a new :class:`Quantity` expressed in ``unit``."""
        return Quantity(convert(self.value, self._unit, unit), unit)

    def __getattr__(self, name: str) -> Numeric:
        # Only invoked when normal lookup (slots/properties/methods) fails, so
        # ``value``/``unit``/``to`` are never shadowed by unit names.
        if name == "_unit":
            # Slot not yet set (e.g. during unpickling); avoid recursion.
            raise AttributeError(name)
        if name in _UNITS:
            return convert(self.value, self._unit, name)
        raise AttributeError(name)

    def __dir__(self) -> list[str]:
        return [*super().__dir__(), *_UNITS]

    # -- arithmetic --------------------------------------------------------
    def _require_same_dim(self, other: "Quantity", op: str) -> None:
        if other.dimension is not self.dimension:
            raise IncompatibleUnitsError(
                f"cannot {op} {self._unit!r} ({self.dimension.value}) and "
                f"{other._unit!r} ({other.dimension.value})"
            )

    def __add__(self, other: object) -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_same_dim(other, "add")
        return Quantity(self.value + other.to(self._unit).value, self._unit)

    def __sub__(self, other: object) -> "Quantity":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_same_dim(other, "subtract")
        return Quantity(self.value - other.to(self._unit).value, self._unit)

    def __mul__(self, k: float) -> "Quantity":
        if isinstance(k, Quantity):
            return NotImplemented  # compound units out of scope
        return Quantity(self.value * k, self._unit)

    __rmul__ = __mul__

    @overload
    def __truediv__(self, k: "Quantity") -> Numeric: ...
    @overload
    def __truediv__(self, k: float) -> "Quantity": ...
    def __truediv__(self, k: "Quantity | float") -> "Quantity | Numeric":
        if isinstance(k, Quantity):
            self._require_same_dim(k, "divide")
            return self.value / k.to(self._unit).value
        return Quantity(self.value / k, self._unit)

    def __neg__(self) -> "Quantity":
        return Quantity(-self.value, self._unit)

    # -- comparison --------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_same_dim(other, "compare")
        return self.value == other.to(self._unit).value

    def __lt__(self, other: "Quantity") -> "bool | np.ndarray":
        self._require_same_dim(other, "compare")
        return self.value < other.to(self._unit).value

    def __le__(self, other: "Quantity") -> "bool | np.ndarray":
        self._require_same_dim(other, "compare")
        return self.value <= other.to(self._unit).value

    def __gt__(self, other: "Quantity") -> "bool | np.ndarray":
        self._require_same_dim(other, "compare")
        return self.value > other.to(self._unit).value

    def __ge__(self, other: "Quantity") -> "bool | np.ndarray":
        self._require_same_dim(other, "compare")
        return self.value >= other.to(self._unit).value

    __hash__ = None

    def __repr__(self) -> str:
        return f"Quantity({self.value!r}, {self._unit!r})"
