"""
H2 shielding by Hartwig et.al. 2015
DOI:https://doi.org/10.1093/mnras/stv1368
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sympy import Expr

from jaff.errors import ParserError
from jaff.physics.photo_reactions.shielding import _register
from jaff.physics.photo_reactions.shielding._base import ShieldingFunction

from ._utils import shielding

if TYPE_CHECKING:
    from jaff.core.network import Network
    from jaff.core.reaction import Reaction


@_register
class HG2015(ShieldingFunction):
    """Hartwig et al. (2015) H2 self-shielding (``shielding.type = "hg2015"``)."""

    name = "hg2015"
    reaction = "H2._PHOTON__H.H"

    def get_shielding(self, reaction: "Reaction", network: "Network") -> Expr:
        """Return the Hartwig et al. (2015) H2 self-shielding factor.

        Thin wrapper over :func:`shielding` with ``alpha = 1.1``.  Reads the
        optional floors ``shielding.min_ncol`` (cm^-2) and
        ``shielding.min_vdisp`` (cm/s) from the reaction metadata.

        Raises
        ------
        ParserError
            If ``min_ncol`` or ``min_vdisp`` is set to a non-numeric value.
        """
        sprops: dict[str, Any] = reaction.metadata["shielding"]
        if "min_ncol" in sprops and not isinstance(sprops["min_ncol"], (float, int)):
            raise ParserError(
                f"Minimum column density must be a float or int for: {reaction}"
            )
        if "min_vdisp" in sprops and not isinstance(sprops["min_vdisp"], (float, int)):
            raise ParserError(
                f"Minimum velocity dispersion must be a float or int for: {reaction}"
            )

        return shielding(
            alpha=1.1,
            min_ncol=sprops.get("min_ncol", 1e-50),
            min_vdisp=sprops.get("min_vdisp", 1e-50),
        )
