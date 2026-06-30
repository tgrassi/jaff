from typing import TypedDict

kromeFormatProps = TypedDict(
    "kromeFormatProps",
    {
        "format_nline": int,
        "idx": bool,
        "nreact": int,
        "nprod": int,
        "tmin": bool,
        "tmax": bool,
        "rate": bool,
    },
)

prizmoFormatProps = TypedDict(
    "prizmoFormatProps",
    {
        "parse_vars": bool,
    },
)
