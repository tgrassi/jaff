"""KROME ``@format:`` header — declares the column layout for reaction lines."""

import re
from functools import cache

from ..._typing import kromeFormatProps
from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class KromeFormatHeader(NetworkFormat):
    """KROME ``@format:`` header — declares column layout for reaction lines."""

    priority = 10
    name = "krome_format"
    state_key = "krome"

    def default_state(self) -> kromeFormatProps:
        return {
            "format_nline": 0,  # line where @format was declared (0 = not yet seen)
            "idx": True,
            "nreact": 3,
            "nprod": 4,
            "tmin": True,
            "tmax": True,
            "rate": True,
        }

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^\s*@format\s*:(?P<format>.*?)$")

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*@format\s*:\s*"
            r"(?P<idx>(?i:idx)\s*,\s*)?"
            r"(?P<reactants>(?:(?i:R)\s*,\s*)+)"
            r"(?P<products>(?:(?i:P)\s*,\s*)+)"
            r"(?P<tmin>(?i:tmin)\s*,?\s*)?"
            r"(?P<tmax>(?i:tmax)\s*,?\s*)?"
            r"(?P<rate>(?i:rate)\s*)?\s*$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a KROME ``@format:`` header line and update the format descriptor.

        Updates the shared ``"krome"`` state with the field counts and flags
        detected in the format declaration so subsequent reaction lines are
        matched with the correct column counts.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the format line is malformed.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        self.state(ctx).update(
            {
                "format_nline": ctx.nline,
                "idx": bool(local.group("idx")),
                "nreact": local.group("reactants").lower().count("r"),
                "nprod": local.group("products").lower().count("p"),
                "tmin": bool(local.group("tmin")),
                "tmax": bool(local.group("tmax")),
                "rate": bool(local.group("rate")),
            }
        )

    def _handle_errors(self, match: re.Match, ctx: ParseContext) -> None:
        """Raise a descriptive error for a malformed KROME ``@format:`` line."""
        format = match.group("format")
        if format is None:
            ctx.raise_error("Empty @format KROME declerative")

        format = format.strip()
        if not format:
            ctx.raise_error("Empty @format KROME declerative")

        if "," not in format:
            ctx.raise_error(
                "Invalid @format KROME declerative\n"
                "@format decelerative must be separated by ','"
            )

        expected_tokens = {"idx", "R", "P", "tmin", "tmax", "rate"}
        tokens = [token.strip() for token in format.split(",")]
        for token in tokens:
            if token not in expected_tokens:
                ctx.raise_error(
                    f"Invalid token in krome format: {token}\n"
                    f"Supported tokens are {','.join(expected_tokens)}"
                )

        ctx.raise_error("Invalid @format KROME declerative")
