from typing import TypedDict

import numpy as np

units = TypedDict("units", {"photon_energy": str, "cross_section": str})
_equations = TypedDict(
    "_equations",
    {
        "pa": bool,
        "pi": bool,
        "pd": bool,
    },
)

XsecsProps = TypedDict(
    "XsecsProps",
    {
        "units": units,
        "_equations": _equations,
        "photon_energy": np.ndarray | None,
        "photo_absorption": np.ndarray | None,
        "photo_ionization": np.ndarray | None,
        "photo_dissociation": np.ndarray | None,
    },
)
