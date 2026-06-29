"""Base interface for a line-shielding function plugin."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sympy import Expr

if TYPE_CHECKING:
    from ....core.network import Network
    from ....core.reaction import Reaction


class ShieldingFunction(ABC):
    """A single photo-reaction line-shielding model.

    Subclasses live in their own module under ``shielding`` and register
    themselves via the :func:`~.register` decorator, keyed by their ``name``
    (the ``shielding.type`` value used in the network config).  The lookup is a
    dict, so resolving a type to its function is O(1) and independent of import
    order or any directory layout.

    Class attributes
    ----------------
    name : str
        Shielding-type identifier, matched case-insensitively against the
        ``shielding.type`` config value.
    reaction : str | None
        Serialized reaction this function is bound to (a *local* model), or
        ``None`` for a *global* model that applies to any reaction.  A function
        is resolved by the pair ``(reaction, name)`` with a fallback to
        ``(None, name)``, so a local model only matches its own reaction.
    """

    name: str
    reaction: str | None = None

    @abstractmethod
    def get_shielding(self, reaction: "Reaction", network: "Network") -> Expr:
        """Return the dimensionless shielding factor for *reaction*."""
        ...
