"""
TypedDict definitions for the JAFF I/O module.

These types describe the intermediate dictionary representation that
:func:`~jaff.io._io.from_jaff_file` produces and that the
:class:`~jaff.Network` constructor consumes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

from ...core._typing import ReactionProps

if TYPE_CHECKING:
    from ...core import Species

JaffProps = TypedDict(
    "JaffProps",
    {
        "file_name": NotRequired[Path],
        "label": NotRequired[str],
        "species": "Species",
        "reactions": NotRequired[list[ReactionProps]],
    },
)
"""
Typed dictionary produced by :func:`~jaff.io._io.from_jaff_file`.

Fields
------
file_name : pathlib.Path, optional
    Original source path stored in the ``.jaff`` payload.
label : str, optional
    Human-readable network name.
species : Species
    The deserialized species collection.
reactions : list of ReactionProps, optional
    List of raw reaction property dicts (each suitable for passing to
    the :class:`~jaff.core.Reaction` constructor).
"""
