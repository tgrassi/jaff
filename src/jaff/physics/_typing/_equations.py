from typing import TypedDict

from sympy import Basic

RadiationGroupReactionProps = TypedDict(
    "RadiationGroupReactionProps",
    {
        "k": Basic,
        "xsec": float | None,
        "xsec_frac": float,
        "delta_rad": float,
    },
)
