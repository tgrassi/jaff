import re
from typing import Callable, TypedDict

patternProps = TypedDict(
    "patternProps",
    {
        "global_re": re.Pattern,
        "local_re": re.Pattern,
        "handler": Callable[..., None],
    },
)

uncompiledPatternProps = TypedDict(
    "uncompiledPatternProps",
    {
        "global_re": str,
        "local_re": str,
        "handler": Callable[..., None],
    },
)

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

networkFormatProps = TypedDict(
    "networkFormatProps",
    {
        "prizmo": prizmoFormatProps,
        "krome": kromeFormatProps,
    },
)

parsedListProps = TypedDict(
    "parsedListProps",
    {
        "r": list[str],
        "p": list[str],
        "tmin": float | None,
        "tmax": float | None,
        "rate": str,
        "string": str,
    },
)
