"""UDFA (UMIST) format: colon-delimited fixed-column reaction database."""

import re
from functools import cache

from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class UdfaReaction(NetworkFormat):
    """UDFA colon-delimited reaction line."""

    priority = 50
    name = "udfa"

    SPECIAL_MAP = {
        "CR": "_CR",
        "CRP": "_CRP",
        "CRPHOT": "_CRPHOT",
        "PHOTON": "_PHOTON",
    }

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^(?!\s*[!#@]).*:.*$")

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*\d+\s*:"
            r"\s*(?P<rtype>[^:]*?)\s*:"
            r"\s*(?P<reactants>(?:[^:]*:){2})"
            r"\s*(?P<products>(?:[^:]*:){4})"
            r"\s*(?P<flag>[^:]*)\s*:"
            r"\s*(?P<ka>[^:]*)\s*:"
            r"\s*(?P<kb>[^:]*)\s*:"
            r"\s*(?P<kc>[^:]*)\s*:"
            r"\s*(?P<tmin>[^:]*)\s*:"
            r"\s*(?P<tmax>[^:]*?)(?:\s*:.*)?$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a UDFA (UMIST)-format reaction line and append it to the parsed list.

        Extracts the reaction type, reactants, products, rate parameters
        (``ka``, ``kb``, ``kc``), and temperature bounds from the
        colon-delimited UDFA format.  Constructs a rate expression based on
        the reaction type: cosmic-ray (``"CR"``), photo-desorption (``"PH"``),
        or standard Arrhenius.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the line does not match the expected
            UDFA format.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        rtype: str = local.group("rtype")
        reactants: str = local.group("reactants")
        products: str = local.group("products")
        ka: float = float(local.group("ka"))
        kb: float = float(local.group("kb"))
        kc: float = float(local.group("kc"))
        tmin: float = float(local.group("tmin"))
        tmax: float = float(local.group("tmax"))

        t_min: None | float = tmin if tmin > 0 else None
        t_max: None | float = tmax if tmax < 41000.0 else None

        rate_dict = {
            "CR": f"{kc:.2e} * crate",
            "PH": f"{ka:.2e} * exp(-{kc:.2f} * av)",
        }
        rate = f"{ka:.2e}"
        if kb:
            rate = f"{rate} * (tgas / 3e2)**({kb:.2f})"
        if kc:
            rate = f"{rate} * exp(-{kc:.2f} / tgas)"

        if rtype in rate_dict:
            rate = rate_dict[rtype]

        rr = [
            self.SPECIAL_MAP.get(r.strip(), r.strip())
            for r in reactants.split(":")[:-1]
            if r.strip() != ""
        ]
        pp = [
            self.SPECIAL_MAP.get(p.strip(), p.strip())
            for p in products.split(":")[:-1]
            if p.strip() != ""
        ]

        if rtype == "PH" and "_PHOTON" not in rr:
            rr.append("_PHOTON")
        elif rtype == "CR" and not any(cr in rr for cr in ("_CR", "_CRP", "_CRPHOT")):
            rr.append("_CR")

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
        """Raise an error for a malformed UDFA reaction line."""
        ctx.raise_error("Invalid UDFA reaction detected")
