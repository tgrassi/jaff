from typing import TypedDict

from ...types import IndexedList

ExtrasDict = TypedDict(
    "ExtrasDict",
    {
        "cse": IndexedList,
    },
)


IndexedReturn = TypedDict(
    "IndexedReturn",
    {
        "extras": ExtrasDict,
        "expressions": IndexedList,
    },
)
