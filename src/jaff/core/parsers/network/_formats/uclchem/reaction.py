"""UCLCHEM format: comma-delimited reactions with a ``NAN`` sentinel column."""

import re
from functools import cache

from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class UclchemReaction(NetworkFormat):
    """UCLCHEM comma-delimited reaction line (``NAN``-sentinel format)."""

    priority = 70
    name = "uclchem"

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(r"^(?!\s*[!]|(?:\s*#\s)).*,\s*(?i:NAN)\s*(?:,|$)")

    @cache
    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^\s*"
            r"(?=.*,\s*(?i:NAN)\s*(?:,|$))"
            r"(?P<reactants>(?:[#@\w\d\+-]*\s*,\s*){3})"
            r"(?P<products>(?:[#@\w\d\+-]*\s*,\s*){4})"
            r"(?P<ka>[^,]*)\s*,\s*"
            r"(?P<kb>[^,]*)\s*,\s*"
            r"(?P<kc>[^,]*)\s*,\s*"
            r"(?P<tmin>[^,]*)\s*,\s*"
            r"(?P<tmax>[^,]*)\s*,\s*"
            r"(?P<extrapolate>.*?)"
            r"\s*$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a UCLCHEM-format reaction line and append it to the parsed list.

        Extracts reactants, products, rate parameters, temperature bounds, and
        an extrapolation flag from the comma-delimited UCLCHEM format (identified
        by the ``NAN`` sentinel column).  Species names are normalised via
        :meth:`_normalize_species`.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the line does not match the expected
            UCLCHEM format.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        reactants: str = local.group("reactants")
        products: str = local.group("products")
        ka: float = float(local.group("ka"))
        kb: float = float(local.group("kb"))
        kc: float = float(local.group("kc"))
        tmin: float = float(local.group("tmin"))
        tmax: float = float(local.group("tmax"))
        extrapolate: bool = local.group("extrapolate").strip().lower() == "true"

        ignore_species = {
            "CR",
            "CRP",
            "CRPHOT",
            "PHOTON",
            "NAN",
            "",
            "ER",
            "ERDES",
            "FREEZE",
            "H2FORM",
            "BULKSWAP",
            "DESCR",
            "DESOH2",
            "DEUVCR",
            "LH",
            "LHDES",
            "SURFSWAP",
            "THERM",
        }

        t_min: float = 3.0 if extrapolate else tmin
        t_max: float = 1e6 if extrapolate else tmax

        rr: list[str] = [self._normalize_species(r) for r in reactants.split(",")]
        pp: list[str] = [
            self._normalize_species(p)
            for p in products.split(",")
            if p.strip().upper() not in ignore_species
        ]

        rate = "0.0"
        rate_dict = {
            "CRP": f"{ka:.2e} * crate",
            "CRPHOT": f"{ka:.2e} * (tgas/3e2)**({kb:.2f}) * crate",
            "PHOTON": f"{ka:.2e} * fuv * exp(-{kc:.2f} * av)",
            "FREEZE": f"(1e0 + {kb:.2e} * 1.671e-3/tgas/asize)*nuth*sigmah*sqrt(tgas/m)",
        }
        for r in rr:
            if r.upper() in rate_dict:
                rate = rate_dict[r.upper()]
                break
        rr = [r for r in rr if r.strip().upper() not in ignore_species]

        # FIXME: old parser sets rate = "0.0" at the very end
        rate = "0.0"

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
        """Raise an error for a malformed UCLCHEM reaction line."""
        ctx.raise_error("Invalid UCLCHEM reaction detected")

    @staticmethod
    def _normalize_species(s: str) -> str:
        """Normalise a UCLCHEM species token to the JAFF canonical form.

        Transformations applied:
        - ``#X`` → ``X_DUST`` (grain-surface species prefix)
        - ``@X`` → ``X_BULK`` (bulk ice species prefix)
        - ``E-`` → ``e-`` (electron lower-case)
        - ``HE`` → ``He``, ``SI`` → ``Si``, ``CL`` → ``Cl``, ``MG`` → ``Mg``

        Parameters
        ----------
        s : str
            Raw species token from the UCLCHEM file.

        Returns
        -------
        str
            Normalised species name.
        """
        s = s.strip()
        if s.startswith("#"):
            s = s[1:] + "_DUST"
        if s.startswith("@"):
            s = s[1:] + "_BULK"
        if s == "E-":
            s = "e-"

        reps = {"HE": "He", "SI": "Si", "CL": "Cl", "MG": "Mg"}

        for k, v in reps.items():
            s = s.replace(k, v)

        return s
