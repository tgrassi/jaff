import re
from abc import ABC, abstractmethod


class NetworkFormat(ABC):
    """Base interface for a single network-file format plugin.

    Subclasses live in their own module under ``_formats`` and register
    themselves so the engine can discover them.  Priority — not file or import
    order — determines the order in which formats are matched against a line.

    Class attributes
    ----------------
    priority : int
        Match order; lower is tried first.
    name : str
        Unique format identifier.
    state_key : str
        Namespace into ``ParseContext.state`` for this format's mutable props.
        Formats that must share live state (e.g. a ``@format`` header and the
        reaction lines it configures) declare the *same* ``state_key``.  The
        empty string means the format keeps no state.
    """

    priority: int
    name: str
    state_key: str = ""

    def default_state(self) -> dict:
        """Return this format's initial mutable props.

        Merged into ``ParseContext.state[self.state_key]`` once at parser
        construction.  Formats sharing a ``state_key`` have their dicts merged.

        Returns
        -------
        dict
            Initial state for this format (empty by default).
        """
        return {}

    def state(self, ctx) -> dict:
        """Return this format's live state slice from *ctx*.

        Parameters
        ----------
        ctx : ParseContext
            Shared parse context.

        Returns
        -------
        dict
            The mutable dict at ``ctx.state[self.state_key]``; writes are
            visible to every format sharing the same ``state_key``.
        """
        return ctx.state[self.state_key]

    @abstractmethod
    def _global_re(self, ctx) -> re.Pattern:
        """Return the compiled regex used to classify a line as this format."""
        pass

    @abstractmethod
    def _local_re(self, ctx) -> re.Pattern:
        """Return the compiled regex used to extract fields from a line.

        Recomputed per call so it reflects the current ``ctx.state`` (e.g. the
        KROME column counts updated by a ``@format`` header).
        """
        pass

    @abstractmethod
    def handle(self, match: re.Match, ctx) -> None:
        """Process a matched line, mutating *ctx* (append a reaction, update state)."""
        pass
