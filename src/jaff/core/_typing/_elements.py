from typing import TypedDict

ElementProps = TypedDict(
    "ElementProps",
    {
        "name": str,
        "mass": float,
        "atomic_mass": float,
        "protons": int,
        "neutrons": int,
        "electrons": int,
    },
)
