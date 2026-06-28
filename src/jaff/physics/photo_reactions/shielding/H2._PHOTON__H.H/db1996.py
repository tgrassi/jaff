"""
H2 shielding by Draine & Bertoldi 1996
DOI:https://ui.adsabs.harvard.edu/link_gateway/1996ApJ...468..269D/doi:10.1086/177689
"""

from typing import Any

from sympy import Expr

from ..... import Network, Reaction
from .....errors import ParserError
from ._utils import shielding


def get_shielding(reaction: Reaction, network: Network) -> Expr:
    """Return the Draine & Bertoldi (1996) H2 self-shielding factor.

    Thin wrapper over :func:`shielding` with ``alpha = 2.0``.  Reads the
    optional floors ``shielding.min_ncol`` (cm^-2) and ``shielding.min_vdisp``
    (cm/s) from the reaction metadata.

    Parameters
    ----------
    reaction : Reaction
        Reaction to shield; provides the ``shielding`` metadata.
    network : Network
        Owning network (unused; kept for the shielding-function interface).

    Returns
    -------
    sympy.Expr
        Dimensionless self-shielding factor.

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
        alpha=2.0,
        min_ncol=sprops.get("min_ncol", 1e-50),
        min_vdisp=sprops.get("min_vdisp", 1e-50),
    )
