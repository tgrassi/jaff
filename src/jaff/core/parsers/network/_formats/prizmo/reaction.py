"""PRIZMO arrow-notation reaction line."""

import re
from functools import cache

from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class PrizmoReaction(NetworkFormat):
    """PRIZMO arrow-notation reaction line."""

    priority = 40
    name = "prizmo"

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^(?!\s*[!#]).*->.*$")

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*"
            r"(?P<reactants>[\w\+\-\s]+)"
            r"\s*->\s*"
            r"(?P<products>[\w\+\-\s]+)"
            r"\s*\[\s*"
            r"(?P<tmin>[^,\]]*)?"
            r"\s*,?\s*"
            r"(?P<tmax>[^,\]]*)?"
            r"\s*\]\s*"
            r"(?P<rate>.*)"
            r"\s*$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a PRIZMO-format reaction line and append it to the parsed list.

        Extracts reactants, products, optional temperature bounds, and rate
        expression from the ``R1 + R2 -> P1 + P2 [tmin, tmax] rate`` pattern.
        Applies species-name normalisation (``HE`` → ``He``, ``E`` → ``e-``,
        ``GRAIN0`` → ``GRAIN``) and converts ``user_crflux``/``user_av``
        aliases to canonical JAFF symbols.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the line does not match the expected
            PRIZMO format.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        reactants: str = local.group("reactants")
        products: str = local.group("products")
        tmin: str | None = local.group("tmin")
        tmax: str | None = local.group("tmax")
        rate: str = local.group("rate").strip()

        reactants = (
            reactants.replace("HE", "He")
            .replace(" E", " e-")
            .replace("E ", "e- ")
            .replace("GRAIN0", "GRAIN")
        )
        products = (
            products.replace("HE", "He")
            .replace(" E", " e-")
            .replace("E ", "e- ")
            .replace("GRAIN0", "GRAIN")
        )

        rr: list[str] = [r.strip() for r in reactants.split(" + ")]
        pp: list[str] = [p.strip() for p in products.split(" + ")]

        t_min: float | None = (
            float(tmin.strip().replace("d", "e")) if tmin and tmin.strip() else None
        )
        t_min = t_min if (t_min is not None and t_min > 0) else None

        t_max: float | None = (
            float(tmax.strip().replace("d", "e")) if tmax and tmax.strip() else None
        )
        t_max = t_max if (t_max is not None and t_max < 1e8) else None

        rate = rate.replace("user_crflux", "crate").replace("user_av", "av")

        ctx.parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "string": ctx.line.strip(),
            }
        )

    def _handle_errors(self, match: re.Match, ctx: ParseContext) -> None:
        """Raise an error for a malformed PRIZMO reaction line."""
        ctx.raise_error("Invalid PRIZMO reaction detected")
