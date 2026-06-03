from typing import TYPE_CHECKING, TypedDict

from sympy import Basic

if TYPE_CHECKING:
    from ...physics._typing._photochemistry import XsecsProps
    from .. import Network, Reaction, Specie, Species
else:
    Specie = "Specie"
    Species = "Species"
    Reaction = "Reaction"
    Network = "Network"


ReactionProps = TypedDict(
    "ReactionProps",
    {
        "reactants": list["Specie"],
        "products": list["Specie"],
        "rate": Basic,
        "dE": Basic,
        "dRad": Basic,
        "custom_rad_rate": bool,
        "tmin": float | None,
        "tmax": float | None,
        "original_string": str,
        "xsecs_dict": "XsecsProps",
    },
)
