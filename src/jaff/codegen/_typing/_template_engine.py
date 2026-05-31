"""TypedDict definitions for TemplateParser internal data structures."""

from typing import Any, Callable, TypedDict

IdxSpanResult = TypedDict(
    "IdxSpanResult",
    {
        "offset": list[int],
        "span": list[tuple[int, int]],
    },
)
"""Result of scanning a template line for ``$idx$`` tokens.

Keys
----
offset : list[int]
    Integer arithmetic offsets extracted from each token (e.g. ``+1`` in
    ``$idx+1$``).  ``0`` when no offset suffix is present.
span : list[tuple[int, int]]
    ``(start, end)`` character positions of each ``$idx*$`` token in the
    scanned line, in left-to-right order.
"""


CommandProps = TypedDict(
    "CommandProps",
    {
        "func": Callable[..., Any],
        "props": dict[str, dict[str, Any]],
    },
)
"""Handler definition for a single JAFF template directive.

Keys
----
func : Callable[..., Any]
    Top-level handler invoked when the directive keyword (``SUB``,
    ``REPEAT``, ``GET``, ``HAS``, ``REDUCE``, ``END``) is encountered.
props : dict[str, dict[str, Any]]
    Per-token property sub-dictionaries used by the handler to resolve
    concrete values (e.g. species count, reaction index, mass).  Each
    entry maps a token name to a ``{"func": callable, ...}`` dict.
"""
