import logging
from pathlib import Path

from sympy import Basic

from .._typing import parsedListProps
from .....errors import ParserError


class ParseContext:
    """Shared mutable state threaded through every :class:`NetworkFormat`.

    A single instance is created per parse and passed by reference to every
    format.  It owns the line cursor, the resolved global symbol map, the
    accumulating parsed-reaction list, and a generic ``state`` store.  It holds
    *no* format-specific knowledge: each format seeds and reads its own slice of
    ``state`` under its declared ``state_key``.

    Parameters
    ----------
    file : Path
        Network file being parsed (used for error context).
    logger : logging.Logger
        Logger for non-fatal warnings raised by formats.
    globals_ : dict[str, Basic]
        Global symbolic constants; formats add ``@var`` / ``VARIABLES`` entries.
    parsed_list : list[parsedListProps]
        Accumulator; formats append one dict per reaction.
    state : dict[str, dict]
        Per-format mutable props, keyed by ``NetworkFormat.state_key``.  Built
        once at construction from each format's ``default_state()``.

    Attributes
    ----------
    line : str
        Current line text, updated by the engine before each dispatch.
    nline : int
        Current 1-based line number.
    """

    def __init__(
        self,
        file: Path,
        logger: logging.Logger,
        globals_: dict[str, Basic],
        parsed_list: list[parsedListProps],
        state: dict[str, dict],
    ):
        self.file: Path = file
        self.logger: logging.Logger = logger
        self.globals: dict[str, Basic] = globals_
        self.parsed_list: list[parsedListProps] = parsed_list
        self.state: dict[str, dict] = state
        self.line: str = ""
        self.nline: int = 0

    def raise_error(self, message: str, **kwargs) -> None:
        """Raise a :exc:`~jaff.errors.ParserError` with current file/line context.

        Parameters
        ----------
        message : str
            Human-readable description of the error.
        **kwargs
            Extra keyword arguments forwarded to :class:`~jaff.errors.ParserError`.

        Raises
        ------
        ParserError
            Always raised.
        """
        raise ParserError(message, self.line, self.nline, self.file, **kwargs)
