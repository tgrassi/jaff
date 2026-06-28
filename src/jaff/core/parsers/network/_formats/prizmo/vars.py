"""PRIZMO ``VARIABLES { }`` block lines and variable assignments."""

import re
from functools import cache

from sympy import parse_expr

from ......common import f90_convert
from ..._typing import prizmoFormatProps
from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class PrizmoVars(NetworkFormat):
    """PRIZMO ``VARIABLES { }`` block lines and variable assignments."""

    priority = 30
    name = "prizmo_vars"
    state_key = "prizmo"

    def default_state(self) -> prizmoFormatProps:
        return {"parse_vars": False}

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*(?:"
            r"(?:(?i:variables)\s*\{|\})(?P<segment>.*?)"
            r"|"
            r"(?P<assignment>\w+\s*=.*?)"
            r")\s*$"
        )

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*(?P<begin>(?i:variables)\s*\{)\s*$"
            r"|"
            r"^\s*(?P<end>\}\s*)$"
            r"|"
            r"^\s*(?P<var>\w+)\s*=\s*\s*(?P<expr>.*?)\s*$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Handle a PRIZMO ``VARIABLES { }`` block line or variable assignment.

        Toggles ``parse_vars`` on ``VARIABLES {`` and ``}`` tokens, and stores a
        parsed SymPy expression for any ``var = expr`` line encountered while
        inside the block.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the line is malformed.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        assert local is not None

        if local.group("begin"):
            self.state(ctx)["parse_vars"] = True
            return

        if local.group("end"):
            self.state(ctx)["parse_vars"] = False
            return

        if local.group("var") and local.group("expr") and self.state(ctx)["parse_vars"]:
            try:
                ctx.globals[local.group("var").lower()] = parse_expr(
                    f90_convert(local.group("expr").lower())
                )

            except (SyntaxError, NameError, TypeError):
                ctx.logger.warning(
                    f"Skipping variable: {local.group('var')}\n"
                    f"at line: {ctx.nline} since the expression is invalid sympy syntax"
                )

    def _handle_errors(self, match: re.Match, ctx: ParseContext) -> None:
        """Raise a descriptive error for a malformed PRIZMO variables section line."""
        segment = match.group("segment")
        assignment = match.group("assignment")

        if segment is None and assignment is None:
            ctx.raise_error("Invalid PRIZMO variable section")

        if assignment is not None:
            if not self.state(ctx)["parse_vars"]:
                ctx.raise_error(
                    "PRIZMO variable assignment found outside VARIABLES block"
                )

            var_name, expr = assignment.split("=", 1)
            var_name = var_name.strip()
            expr = expr.strip()

            if not var_name.isidentifier():
                ctx.raise_error(f"Invalid variable name '{var_name}'")

            if not expr:
                ctx.raise_error("Expression cannot be empty")

        segment = segment.strip()
        if segment:
            ctx.raise_error("Extra characters found after PRIZMO block declarative")
