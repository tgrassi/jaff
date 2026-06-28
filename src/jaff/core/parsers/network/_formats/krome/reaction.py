"""KROME comma-delimited reaction line."""

import re
from functools import cache

from ......common import f90_convert
from .. import register
from .._base import NetworkFormat
from .._context import ParseContext


@register
class KromeReaction(NetworkFormat):
    """KROME comma-delimited reaction line."""

    priority = 60
    name = "krome"
    state_key = "krome"

    @cache
    def _global_re(self, ctx: ParseContext) -> re.Pattern:
        return re.compile(
            r"^(?!\s*[!#@])"
            r"(?!.*,\s*(?i:NAN)\s*(?:,|$))"
            r"(?=.*,)"
            r"(?P<segment>.*)$"
        )

    def _local_re(self, ctx: ParseContext) -> re.Pattern:
        props = self.state(ctx)

        return re.compile(
            r"^\s*"
            r"(?!.*,\s*(?i:NAN)\s*(?:,|$))"
            + (r"(?P<idx>[^,]*)\s*,\s*" if props["idx"] else "")
            + rf"(?P<reactants>(?:[^,]*\s*,\s*){{{props['nreact']}}})"
            + rf"(?P<products>(?:[^,]*\s*,\s*){{{props['nprod']}}})"
            + (r"(?P<tmin>[^,]*)\s*,\s*" if props["tmin"] else "")
            + (r"(?P<tmax>[^,]*)\s*,\s*" if props["tmax"] else "")
            + (r"(?P<rate>.*)" if props["rate"] else "")
            + r"\s*$"
        )

    def handle(self, match: re.Match, ctx: ParseContext) -> None:
        """Parse a KROME-format reaction line and append it to the parsed list.

        Extracts the index, reactants, products, temperature bounds, and rate
        expression from the comma-delimited KROME format.  Applies species
        normalisation (``E``/``e`` → ``e-``, ``g`` → empty, ``HE`` → ``He``)
        and converts ``user_crflux``/``user_av`` aliases.  Fortran exponent
        notation is converted to Python notation via :func:`~jaff.common.f90_convert`.

        Raises
        ------
        ParserError
            Via :meth:`_handle_errors` if the line structure is inconsistent
            with the declared KROME format.
        """
        local = self._local_re(ctx).match(ctx.line)
        if not local:
            self._handle_errors(match, ctx)

        reactants: str = local.group("reactants")
        products: str = local.group("products")
        tmin: str = local.groupdict().get("tmin", "").strip().lower()
        tmax: str = local.groupdict().get("tmax", "").strip().lower()
        rate: str = local.groupdict().get("rate", "").strip()

        rr: list[str] = [r.strip() for r in reactants.split(",")[:-1]]
        pp: list[str] = [p.strip() for p in products.split(",")[:-1]]

        if len(rr) != self.state(ctx)["nreact"]:
            ctx.raise_error(
                "Invalid KROME line detected\n"
                f"Expected {self.state(ctx)['nreact']} reactants\n"
                f"from line {self.state(ctx)['format_nline']}.\n"
                f"Instead got {len(rr)} reactants"
            )

        if len(pp) != self.state(ctx)["nprod"]:
            ctx.raise_error(
                "Invalid KROME line detected\n"
                f"Expected {self.state(ctx)['nprod']} products \n"
                f"from line {self.state(ctx)['format_nline']}.\n"
                f"Instead got {len(pp)} products"
            )

        t_min: None | float = None
        t_max: None | float = None

        sp_reps = {"E": "e-", "e": "e-", "g": ""}
        rr = [sp_reps.get(r, r) for r in rr]
        pp = [sp_reps.get(p, p) for p in pp]

        sp_sreps = {"HE": "He"}

        for k, v in sp_sreps.items():
            rr = [x.replace(k, v) for x in rr]
            pp = [x.replace(k, v) for x in pp]

        rr = [r for r in rr if r != ""]
        pp = [p for p in pp if p != ""]

        tminmax_reps = {
            "d": "e",
            ".le.": "",
            ".ge.": "",
            ".lt.": "",
            ".gt.": "",
            ">": "",
            "<": "",
        }

        if tmin != "none" and tmin != "":
            for k, v in tminmax_reps.items():
                tmin = tmin.replace(k, v)
            t_min = float(tmin)

        if tmax != "none" and tmax != "":
            for k, v in tminmax_reps.items():
                tmax = tmax.replace(k, v)
            t_max = float(tmax)

        rate_reps = {
            "user_crflux": "crate",
            "user_crate": "crate",
            "user_av": "av",
        }
        for k, v in rate_reps.items():
            rate = rate.replace(k, v)

        rate = f90_convert(rate)
        if "auto" in rate:
            rate = rate.replace("auto", "PHOTO, 1e99")

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
        """Raise a descriptive error for a malformed KROME reaction line.

        Diagnoses the most likely cause (wrong field count, wrong reactant or
        product count) before falling back to a generic error message.
        """
        segment = match.group("segment").lower()
        props = self.state(ctx)
        num_fields = (
            int(props["idx"])
            + props["nreact"]
            + props["nreact"]
            + int(props["tmin"])
            + int(props["tmax"])
            + int(props["rate"])
        )
        num_fields_detected: int = segment.count(",") + 1

        if num_fields != num_fields_detected:
            ctx.raise_error(
                "Number of fields in KROME reaction doesn't match\n"
                f"Number of fields detected: {num_fields_detected}\n"
                f"Number of fields expected: {num_fields}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        if segment.count("r") != props["nreact"]:
            ctx.raise_error(
                "Expected number of reactants did not match krome format\n"
                f"Number of reactants expected: {props['nreact']}\n"
                f"Number of reactants detected: {segment.count('r')}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        if segment.count("p") != props["nprod"]:
            ctx.raise_error(
                "Expected number of products did not match krome format\n"
                f"Number of products expected: {props['nprod']}\n"
                f"Number of products detected: {props['nprod']}\n"
                + (
                    f"KROME format defined on line: {props['format_nline']}"
                    if props["format_nline"]
                    else ""
                )
            )

        ctx.raise_error("Invalid KROME reaction detected")
