"""
Custom exception classes for the JAFF units subsystem.

Classes
-------
:class:`UnitsError`
    Base class for all errors raised by :mod:`jaff.physics._units`.
:class:`UnknownUnitError`
    Raised when a unit name is not present in the unit registry.
:class:`IncompatibleUnitsError`
    Raised when two units' dimensions cannot be converted or combined (no
    factor ratio and no physics bridge connects them).
"""


class UnitsError(Exception):
    """Base class for all unit errors raised by the units subsystem."""


class UnknownUnitError(UnitsError):
    """Raised when a unit name is not in the registry."""


class IncompatibleUnitsError(UnitsError):
    """Raised when two units' dimensions cannot be converted or combined."""
