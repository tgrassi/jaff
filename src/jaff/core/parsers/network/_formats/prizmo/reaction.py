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

    SPECIAL_MAP = {
        "GRAIN0": "_GRAIN",
        "GRAIN": "_GRAIN",
        "CR": "_CR",
        "CRP": "_CRP",
        "CRPHOT": "_CRPHOT",
        "PHOTON": "_PHOTON",
        "dummy": "_DUMMY",
    }

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
        Applies species-name normalisation (``HE`` → ``He``, ``E`` → ``e-``)
        and exotic pseudo-species normalisation (``GRAIN0``/``GRAIN`` →
        ``_GRAIN``, ``CR`` → ``_CR``, ``PHOTON`` → ``_PHOTON``, ``dummy`` →
        ``_DUMMY``, ...), and converts ``user_crflux``/``user_av`` aliases to
        canonical JAFF symbols.

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
            reactants.replace("HE", "He").replace(" E", " e-").replace("E ", "e- ")
        )
        products = products.replace("HE", "He").replace(" E", " e-").replace("E ", "e- ")

        rr: list[str] = [
            self.SPECIAL_MAP.get(r.strip(), r.strip()) for r in reactants.split(" + ")
        ]
        pp: list[str] = [
            self.SPECIAL_MAP.get(p.strip(), p.strip()) for p in products.split(" + ")
        ]

        t_min: float | None = (
            float(tmin.strip().replace("d", "e")) if tmin and tmin.strip() else None
        )
        t_min = t_min if (t_min is not None and t_min > 0) else None

        t_max: float | None = (
            float(tmax.strip().replace("d", "e")) if tmax and tmax.strip() else None
        )
        t_max = t_max if (t_max is not None and t_max < 1e8) else None

        rate = rate.replace("user_crflux", "crate").replace("user_av", "av")

        if "photo" in rate.lower() and "_PHOTON" not in rr:
            rr.append("_PHOTON")

        ctx.parsed_list.append(
            {
                "r": rr,
                "p": pp,
                "tmin": t_min,
                "tmax": t_max,
                "rate": rate,
                "type": self._reaction_type(rate, rr),
                "string": ctx.line.strip(),
            }
        )

    @staticmethod
    def _reaction_type(rate: str, rr: list[str]) -> str:
        """Conclude the reaction type from the reactants, falling back to rate.

        Structural signals are checked first so the result survives custom
        auxiliary-function rates: a ``_PHOTON`` reactant -> ``"photo"``, a
        cosmic-ray pseudo-species (``_CR``/``_CRP``/``_CRPHOT``) ->
        ``"cosmic_ray"``, three or more real reactants -> ``"3_body"``. Only
        then is the rate inspected (``photo``/``av`` -> ``"photo"``, ``crate``
        -> ``"cosmic_ray"``, ``ntot`` -> ``"3_body"``); otherwise ``"unknown"``.
        """
        if "_PHOTON" in rr:
            return "photo"
        if any(c in rr for c in ("_CR", "_CRP", "_CRPHOT")):
            return "cosmic_ray"
        if sum(1 for r in rr if not r.startswith("_")) >= 3:
            return "3_body"

        r = rate.lower()
        if "photo" in r:
            return "photo"
        if "crate" in r:
            return "cosmic_ray"
        if "av" in r:
            return "photo"
        if "ntot" in r:
            return "3_body"
            
        return "unknown"

    def _handle_errors(self, match: re.Match, ctx: ParseContext) -> None:
        """Raise an error for a malformed PRIZMO reaction line."""
        ctx.raise_error("Invalid PRIZMO reaction detected")
