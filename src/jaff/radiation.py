from typing import TypedDict

import sympy as sp

from .drivers.sqlite import JaffDb
from .reaction import Reaction
from .species import Species

RadiationGroupReactionProps = TypedDict(
    "RadiationGroupReactionProps",
    {
        "k": sp.Basic,
        "xsec": sp.Basic,
        "xsec_frac": sp.Basic,
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
        self.bands: list[int | float | str | sp.Basic] = bands
        self.nbands: int = len(self.bands) - 1
        self.powerlaw_idx: int | float = powerlaw_idx
        self.energy_density: bool = energy_density
        self.c: float = c

        self.__parse_bands()
        self.groups: list[RadiationGroup] = [
            RadiationGroup(lower, self.bands[i + 1], i)
            for i, lower in enumerate(self.bands[:-1])
        ]

    def set_reaction_rate_coefficient(self, reaction: Reaction) -> None:
        xsec = self.get_verner_xsec(reaction.reactants, reaction.products)
        if xsec is None:
            return

        # Set reaction total cross section
        E = sp.Symbol("E")
        xsec_tot = sp.Integral(xsec, (E, self.bands[0], self.bands[-1])).evalf()
        reaction.rad_xsecs = xsec_tot

        n_profile = E ** (self.powerlaw_idx - 2)
        k_tot = sp.Float(0.0)  # Total rate coefficient over all bands

        den = sp.MatrixSymbol(
            "radeden" if self.energy_density else "photden", self.nbands, 1
        )

        for i, lower in enumerate(self.bands[:-1]):
            upper = self.bands[i + 1]
            n_tot = sp.Integral(n_profile, (E, lower, upper)).evalf()
            n_avg = sp.Integral(xsec * n_profile, (E, lower, upper)).evalf() / n_tot
            band_xsec = sp.Integral(xsec, (E, lower, upper)).evalf()
            k = self.c * den[sp.Idx(i)] * n_avg
            k_tot += k

            self.groups[i].props[reaction] = {
                "k": k,
                "xsec": band_xsec,
                "xsec_frac": band_xsec / xsec_tot,
            }

            if self.groups[i].eavg is None:
                self.groups[i].eavg = (
                    sp.Integral(E * n_profile, (E, lower, upper)).evalf() / n_tot
                )

        reaction.rate = k_tot

    def get_verner_xsec(
        self, reactants: list[Species], products: list[Species]
    ) -> sp.Basic | None:
        with JaffDb() as jdb:
            table = jdb.table("verner_cross_sections")
            xsec_present = False
            rows = []
            for reactant in reactants:
                rows = table.rows(conditions=f"Ion = '{reactant}'")
                if rows:
                    xsec_present = True
                    break

        if not xsec_present:
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

    def __parse_bands(self):
        if "inf" in self.bands:
            inf_index = self.bands.index("inf")
            self.bands[inf_index] = sp.oo

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
