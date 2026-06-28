from typing import TYPE_CHECKING, TypedDict

from sympy import Basic, Expr

if TYPE_CHECKING:
    from ...physics.photo_reactions._photochemistry import XsecsProps
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
        "rate": Expr,
        "dE": Basic,
        "dRad": Basic,
        "custom_rad_rate": bool,
        "tmin": float | None,
        "tmax": float | None,
        "original_string": str,
        "xsecs_dict": "XsecsProps",
    },
)
