from typing import TypedDict

from sympy import Basic

RadiationGroupReactionProps = TypedDict(
    "RadiationGroupReactionProps",
    {
        "k": Basic,
        "xsec": Basic | None,
        "xsec_frac": Basic,
        "delta_rad": Basic,
    },
)
