"""TypedDict definitions for Codegen structured return values."""

from typing import TypedDict

from ...types import IndexedList

ExtrasDict = TypedDict(
    "ExtrasDict",
    {
        "cse": IndexedList,
    },
)
"""Extra data returned alongside the main code-generation expressions.

Keys
----
cse : IndexedList
    CSE temporaries as ``(idx, expr_str)`` pairs produced by
    :func:`sympy.cse`.
"""


IndexedReturn = TypedDict(
    "IndexedReturn",
    {
        "extras": ExtrasDict,
        "expressions": IndexedList,
    },
)
"""Structured return type for indexed code-generation methods.

Keys
----
extras : ExtrasDict
    Supplementary data, including CSE temporaries under ``extras["cse"]``.
expressions : IndexedList
    Primary ``(index_list, expression_str)`` pairs produced by the
    generator, one per reaction, species, or Jacobian element.
"""
