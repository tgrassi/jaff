import sympy as sp

from .drivers.sqlite import JaffDb
from .reaction import Reaction
from .species import Species


class RadiationGroup:
    def __init__(self, lower, upper, index):
        self.index: int = index
        self.lower: float | int = lower
        self.upper: float | int | sp.Basic = upper
        self.band: tuple = (lower, upper)
        self.dE: float | sp.Basic = self.upper - self.lower
        self.k: dict[Reaction, sp.Basic] = {}  # Rate coeffiecients for each reaction

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

    def total_prate_coeff(
        self,
        reactants: list[Species],
        products: list[Species],
    ) -> tuple[sp.Basic | None, list[sp.Basic] | None]:
        with JaffDb() as jdb:
            table = jdb.table("verner_cross_sections")
            xsec_present = False
            rows = []
            for reactant in reactants:
                rows = table.rows(conditions=f"Ion = '{str(reactant)}'")
                if rows:
                    xsec_present = True
                    break

            if not xsec_present:
                return None, None

        E = sp.Symbol("E")
        n_profile = E ** (self.powerlaw_idx - 2)
        k_total = sp.Float(0.0)  # Total rate coefficient over all bands
        ks: list[sp.Basic] = [
            sp.Float(0.0) for _ in range(self.nbands)
        ]  # Individual rate coefficients
        xsec = sp.sympify(rows[0]["xsecs"])

        den = sp.MatrixSymbol(
            "radeden" if self.energy_density else "photden", self.nbands, 1
        )

        for i, lower in enumerate(self.bands[:-1]):
            upper = self.bands[i + 1]
            n_tot = sp.Integral(n_profile, (E, lower, upper)).evalf()
            xsec_avg = sp.Integral(xsec * n_profile, (E, lower, upper)).evalf() / n_tot

            if self.energy_density:
                e_avg = sp.Integral(E * n_profile, (E, lower, upper)).evalf() / n_tot
                ks[i] = (
                    self.c * den[sp.Idx(i)] * xsec_avg / e_avg
                )  # This energy average will probably not be there. Will get back to this. Fix this
                k_total += ks[i]

                continue

            ks[i] = self.c * den[sp.Idx(i)] * xsec_avg
            k_total += ks[i]

        return k_total, ks

    def add_reaction_to_group(self, reaction: Reaction, band_coeffs: list[sp.Basic]):
        for group, coeff in zip(self.groups, band_coeffs):
            group.k[reaction] = coeff

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
