from typing import NotRequired, TypedDict

from sympy import Basic

FunctionsDict = TypedDict(
    "FunctionsDict",
    {
        "def": Basic,
        "args": list[Basic],
        "argcomments": dict[str, str],
        "locals": NotRequired[dict[str, Basic]],
    },
)
