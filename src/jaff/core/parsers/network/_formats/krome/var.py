"""KROME ``@var:`` directive — stores a symbolic global expression."""

import re
from functools import cache

from sympy import parse_expr

from ......common import f90_convert
from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class KromeVar(NetworkFormat):
    """KROME ``@var:`` directive — stores a symbolic global expression."""

    priority = 20
    name = "krome_var"

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^\s*@var\s*:(?P<segment>.*?)$")

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^\s*@var\s*:\s*(?P<var>\w+)\s*=\s*\s*(?P<expr>.*?)\s*$")

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a KROME ``@var:`` directive and store the symbolic expression.

        Logs a warning and skips the variable when the expression is not valid
        SymPy syntax (rather than raising a hard error).
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            ctx.raise_error("Invalid KROME variable assignment detected")

        try:
            ctx.globals[local.group("var").lower()] = parse_expr(
                f90_convert(local.group("expr").lower())
            )
        except (SyntaxError, NameError, TypeError):
            ctx.logger.warning(
                f"Skipping variable: {local.group('var')}\n"
                f"at line: {ctx.nline} since the expression is invalid sympy syntax"
            )
