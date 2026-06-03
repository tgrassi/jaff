from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sympy import Basic, sympify

from ..drivers import HDF5, JaffDb
from ._typing import XsecsProps

if TYPE_CHECKING:
    from ..core import Reaction


def get_verner_xsec(reaction: Reaction) -> Basic | None:
    """
    Query the JAFF database for the Verner photoionisation cross section.

    Verner cross sections are analytic fits to photoionisation cross
    sections from Verner et al. (1996) stored as SymPy-parseable strings
    in the ``verner_cross_sections`` SQLite table.

    Parameters
    ----------
    reaction : Reaction
        Reaction whose serialised key is used as the database look-up.

    Returns
    -------
    sympy.Basic or None
        The SymPy expression for σ(E) if the reaction is found, or
        ``None`` if no entry exists (e.g. for non-photoionisation
        reactions).

    Notes
    -----
    The expression uses the symbol ``E`` (photon energy in erg) as the
    independent variable and returns cross sections in cm².

    References
    ----------
    Verner, D. A. et al. 1996, ApJ, 465, 487
    """
    with JaffDb() as jdb:
        table = jdb.table("verner_cross_sections")
        rows: list = table.rows(conditions=f"reaction = '{reaction.serialized}'")

    if not rows:
        return None

    # Convert the stored string representation back to a SymPy expression.
    return sympify(rows[0]["xsecs"])


def get_xsec(reaction: Reaction) -> XsecsProps | None:
    with JaffDb() as jdb:
        table = jdb.table("photo_reaction_cross_sections")
        rows: list = table.rows(conditions=f"reaction = '{reaction.serialized}'")

    if not rows:
        return None

    row = rows[0]
    loc: str = row["leiden"] if row["leiden"] else row["norad"]
    jaff_dir = Path(__file__).parent.parent.resolve()
    h5group = str(jaff_dir / loc)
    pr_xsec = HDF5().to_dict(h5group)

    xsecs: XsecsProps = {
        "units": {
            "photon_energy": "eV",
            "cross_section": "cm^2",
        },
        "_equations": {
            "pa": bool(row["photo_absorption"]),
            "pi": bool(row["photo_ionization"]),
            "pd": bool(row["photo_dissociation"]),
        },
        "photon_energy": pr_xsec.get("photon_energy", {}).get("_data", None),
        "photo_absorption": pr_xsec.get("photoabsorption", {}).get("_data", None),
        "photo_ionization": pr_xsec.get("photoionization", {}).get("_data", None),
        "photo_dissociation": pr_xsec.get("photodissociation", {}).get("_data", None),
    }

    return xsecs
