from typing import NotRequired, TypedDict

from sympy import Basic

AuxiliaryFunctionsDict = TypedDict(
    "AuxiliaryFunctionsDict",
    {
        "def": Basic,
        "args": list[Basic],
        "argcomments": dict[str, str],
        "locals": NotRequired[dict[str, Basic]],
    },
)
