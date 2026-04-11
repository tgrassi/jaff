from typing import TypedDict, cast

import sympy as sp

from .drivers.sqlite import JaffDb
from .reaction import Reaction
from .utils.integrators import smart_integrate

RadiationGroupReactionProps = TypedDict(
    "RadiationGroupReactionProps",
    {
        "k": sp.Basic,
        "xsec": sp.Basic | None,
        "xsec_frac": sp.Basic,
        "delta_rad": sp.Basic,
    },
)


class RadiationGroup:
    def __init__(self, lower, upper, index):
        self.index: int = index
        self.lower: float | int = lower
        self.upper: float | int | sp.Basic = upper
        self.band: tuple = (lower, upper)
        self.dE: float | sp.Basic = self.upper - self.lower
        self.props: dict[
            Reaction, RadiationGroupReactionProps
        ] = {}  # Rate coeffiecients for each reaction
        self.eavg: sp.Basic | None = None

    def __repr__(self):
        return f"Rad_group({self.index}, band={self.band})"

    def __str__(self):
        return f"Radiation group {self.index}"


class Radiation:
    def __init__(
        self,
        bands: list[int | float | str | sp.Basic],
        powerlaw_idx: int | float,
        energy_density: bool,
        c: float,
    ):
        self.bands: list[int | float | sp.Basic] = []
        self.powerlaw_idx: int | float = powerlaw_idx
        self.energy_density: bool = energy_density
        self.c: float = c

        self.__parse_bands(bands)
        self.nbands: int = len(self.bands) - 1
        self.groups: list[RadiationGroup] = [
            RadiationGroup(lower, self.bands[i + 1], i)
            for i, lower in enumerate(self.bands[:-1])
        ]

    def set_reaction_rate_coefficient(self, reaction: Reaction) -> None:
        xsec = self.get_verner_xsec(reaction)
        if xsec is None:
            return

        # Set reaction total cross section
        E = sp.Symbol("E")
        xsec_tot = smart_integrate(xsec, E, (self.bands[0], self.bands[-1]))
        reaction.rad_xsecs = xsec_tot

        n_profile = E ** (self.powerlaw_idx - 2)
        k_tot = sp.Float(0.0)  # Total rate coefficient over all bands

        den = sp.MatrixSymbol(
            "radeden" if self.energy_density else "photden", self.nbands, 1
        )

        for i, lower in enumerate(self.bands[:-1]):
            upper = self.bands[i + 1]
            n_tot = smart_integrate(n_profile, E, (lower, upper))
            xsec_avg = smart_integrate(xsec * n_profile, E, (lower, upper)) / n_tot
            band_xsec = smart_integrate(xsec, E, (lower, upper))
            delta_rad_band = smart_integrate(reaction.dRad_dt, E, (lower, upper))
            k = self.c * den[sp.Idx(i)] * xsec_avg

            self.groups[i].props[reaction] = {
                "k": k,
                "xsec": band_xsec,
                "xsec_frac": band_xsec / xsec_tot,
                "delta_rad": delta_rad_band,
            }

            if self.groups[i].eavg is None:
                self.groups[i].eavg = (
                    smart_integrate(E * n_profile, E, (lower, upper)) / n_tot
                )

            k_tot += k / (self.groups[i].eavg if self.energy_density else 1)

        reaction.rate = k_tot

    def set_custom_rate(self, reaction: Reaction) -> None:
        # Expects E to be the energy symbol for custom delta_rad aux functions
        # delta_rad must also be in units of ev
        E = sp.Symbol("E")
        delta_rad_total = smart_integrate(
            reaction.dRad_dt, E, (self.bands[0], self.bands[-1])
        )
        delta_rad_total_is_zero = delta_rad_total.equals(0)

        for i, lower in enumerate(self.bands[:-1]):
            upper = self.bands[i + 1]
            delta_rad_band = smart_integrate(reaction.dRad_dt, E, (lower, upper))
            xsec_frac = (
                sp.Float(0.0)
                if delta_rad_total_is_zero
                else delta_rad_band / delta_rad_total
            )
            k = reaction.rate * xsec_frac

            self.groups[i].props[reaction] = {
                "k": k,
                "xsec": None,
                "xsec_frac": xsec_frac,
                "delta_rad": delta_rad_band,
            }

    def get_verner_xsec(self, reaction: Reaction) -> sp.Basic | None:
        with JaffDb() as jdb:
            table = jdb.table("verner_cross_sections")
            rows: list = table.rows(conditions=f"reaction = '{reaction.serialized}'")

        if not rows:
            return None

        return sp.sympify(rows[0]["xsecs"])

    def ordered_index(self, idx: int, order: int) -> tuple[int, int]:
        ei = 2 * idx  # Energy index
        fi = 2 * idx + 1  # FLux index

        if order == 1:
            ei = 2 * idx + 1
            fi = 2 * idx
        elif order == 2:
            ei = idx
            fi = self.nbands + idx
        elif order == 3:
            ei = self.nbands + idx
            fi = idx

        return ei, fi

    def __parse_bands(self, bands: list[float | int | str | sp.Basic]):
        if "inf" in bands:
            inf_index = bands.index("inf")
            bands[inf_index] = sp.oo

        self.bands = cast(list[int | float | sp.Basic], bands)

        if self.energy_density:
            pl_index: float = float(self.powerlaw_idx) - 1.0
            if pl_index == -1.0:
                if (
                    isinstance(self.bands[0], (float, int))
                    and float(self.bands[0]) == 0.0
                ):
                    raise RuntimeError(
                        f"The integral for average energy will diverge since the radiation band starts from bands[0]: {self.bands[0]}\n"
                        "Please try a non-zero value"
                    )
                if self.bands[-1] == sp.oo:
                    raise RuntimeError(
                        f'The integral for average energy will diverge since the radiation band ends at bands[{len(self.bands) - 1}]: "inf"\n'
                        "Please try a non-infinite value or change the power_law_index"
                    )
            elif pl_index + 1.0 > 0.0:
                if self.bands[-1] == sp.oo:
                    raise RuntimeError(
                        f'The integral for average energy will diverge since the radiation band ends at bands[{len(self.bands) - 1}]: "inf"\n'
                        "Please try a non-infinite value or change the power_law_index"
                    )
            elif pl_index + 1.0 < 0.0:
                if (
                    isinstance(self.bands[0], (float, int))
                    and float(self.bands[0]) == 0.0
                ):
                    raise RuntimeError(
                        f"The integral for average energy will diverge since the radiation band starts from bands[0]: {self.bands[0]}\n"
                        "Please try a non-zero value"
                    )
