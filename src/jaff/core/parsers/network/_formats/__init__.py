"""Plugin registry for network-file format parsers.

Each supported format lives in its own subpackage (``krome``, ``prizmo``,
``udfa``, ``uclchem``, ``kida``) and registers one or more
:class:`~._base.NetworkFormat` subclasses via the :func:`register` decorator.
The engine discovers them through :func:`all_formats`, which returns the
formats sorted by their declared ``priority`` — so match order is independent
of file or import order.

Adding a new format requires only a new subpackage with a ``@register``-ed
class; no engine or :class:`~._context.ParseContext` edits.
"""

from ._base import NetworkFormat
from ._context import ParseContext

_REGISTRY: list[type[NetworkFormat]] = []


def register(cls: type[NetworkFormat]) -> type[NetworkFormat]:
    """Register *cls* as an available network format.

    Parameters
    ----------
    cls : type[NetworkFormat]
        The format class to register.

    Returns
    -------
    type[NetworkFormat]
        *cls* unchanged, so the decorator is transparent.
    """
    _REGISTRY.append(cls)

    return cls


def all_formats() -> list[NetworkFormat]:
    """Instantiate every registered format, sorted by priority.

    Importing the format subpackages here triggers their ``@register``
    decorators, populating :data:`_REGISTRY`.

    Returns
    -------
    list[NetworkFormat]
        One instance per registered format, in ascending priority order
        (lower priority is matched against each line first).
    """
    from jaff.common._helper import import_subpackages

    import_subpackages(__name__)

    return sorted((cls() for cls in _REGISTRY), key=lambda fmt: fmt.priority)


def build_state(formats: list[NetworkFormat]) -> dict[str, dict]:
    """Build the shared per-format state store for a :class:`ParseContext`.

    Merges each format's :meth:`~._base.NetworkFormat.default_state` into a
    dict keyed by ``state_key``.  Formats sharing a ``state_key`` (e.g. a KROME
    ``@format`` header and the reaction lines it configures) share one dict.

    Parameters
    ----------
    formats : list[NetworkFormat]
        Formats whose initial state to collect.

    Returns
    -------
    dict[str, dict]
        Mapping of ``state_key`` to its merged initial state.
    """
    state: dict[str, dict] = {}
    for fmt in formats:
        if fmt.state_key:
            state.setdefault(fmt.state_key, {}).update(fmt.default_state())

    return state


__all__ = ["NetworkFormat", "ParseContext", "register", "all_formats", "build_state"]
