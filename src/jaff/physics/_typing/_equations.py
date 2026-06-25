from typing import TypedDict

from sympy import Expr

RadiationGroupReactionProps = TypedDict(
    "RadiationGroupReactionProps",
    {
        "k": Expr,
        "xsec": float | None,
        "xsec_frac": float,
        "delta_rad": float,
    },
)
