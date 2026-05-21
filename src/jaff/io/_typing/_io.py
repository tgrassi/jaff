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
