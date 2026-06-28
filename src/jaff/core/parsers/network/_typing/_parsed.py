from typing import TypedDict

parsedListProps = TypedDict(
    "parsedListProps",
    {
        "r": list[str],
        "p": list[str],
        "tmin": float | None,
        "tmax": float | None,
        "rate": str,
        "type": str,
        "string": str,
    },
)
