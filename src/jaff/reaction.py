from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import numpy as np
from sympy import (
    Basic,
    Function,
    ccode,
    cxxcode,
    fcode,
    julia_code,
    lambdify,
    pycode,
    rcode,
    rust_code,
    symbols,
    sympify,
)

from .core.logger import JaffLogger
from .physics import constants
from .types import Catalogue

if TYPE_CHECKING:
    from .species import Specie


class Reaction:
    def __init__(
        self,
        reactants: list[Specie],
        products: list[Specie],
        rate: Basic,
        tmin: float | None,
        tmax: float | None,
        dE: Basic,
        dRad_dt: Basic,
        original_string: str,
        index: int,
        errors: bool = False,
    ):
        self.logger = JaffLogger().get_logger()
        self.reactants: list[Specie] = reactants
        self.products: list[Specie] = products
        self.rate: Basic = rate
        self.tmin: float | None = tmin
        self.tmax: float | None = tmax
        self.dE: Basic = dE
        self.dRad_dt: Basic = dRad_dt
        self.custom_rad_rate: bool = False
        self.rad_xsecs: float | None = None
        # dictionary {"energy": [], "xsecs": []}, energy in erg, xsecs in cm^2
        self.xsecs_dict: dict | None = None
        self.original_string = original_string
        # Add verbatim property for backward compatibility
        self.verbatim: str = self.get_verbatim()
        self.index: int = index

        self.check(errors)
        self.serialized_exploded: str = self.serialize_exploded()
        self.serialized: str = self.serialize()
        self.metadata: dict = {}

        # Add type metadata to reaction
        self.guess_type()

    def __repr__(self):
        return (
            f"Reaction({self.verbatim}, tmin={self.tmin}, tmax={self.tmax}, dE={self.dE})"
        )

    def __str__(self):
        return self.verbatim

    def guess_type(self) -> str:
        rtype = "unknown"

        if type(self.rate) is str:
            if "photo" in self.rate:
                rtype = "photo"
        else:
            # Check if rate is a photorates Function
            if hasattr(self.rate, "func") and isinstance(
                self.rate.func, type(Function("f"))
            ):
                if self.rate.func.__name__ == "photorates":
                    rtype = "photo"
            elif self.rate.has(symbols("crate")):
                rtype = "cosmic_ray"
            elif self.rate.has(symbols("av")):
                rtype = "photo_av"
            elif self.rate.has(symbols("ntot")):
                rtype = "3_body"

        self.metadata["type"] = rtype

        return rtype

    def is_same(self, other: "Reaction") -> bool:
        return self.serialized == other.serialized

    def is_isomer_version(self, other: "Reaction") -> bool:
        # compare serialized forms (ignore isomers)
        is_same_serialized = self.serialized_exploded == other.serialized_exploded

        # compare actual species names (consider isomers)
        rp1 = sorted([x.name for x in self.reactants + self.products])
        rp2 = sorted([x.name for x in other.reactants + other.products])
        has_different_species_names = rp1 != rp2

        return is_same_serialized and has_different_species_names

    # note that the serialized form uses the exploded form of species names
    # H2O+ will be serialzed as +/H/H/O, hence this will be identical to OH2+
    def serialize_exploded(self) -> str:
        sr = "_".join(sorted([x.serialized for x in self.reactants]))
        sp = "_".join(sorted([x.serialized for x in self.products]))

        return f"{sr}__{sp}"

    # this version uses the names and not the exploded forms of the species
    def serialize(self) -> str:
        # serialize the reaction in the form R__P_P
        sr = "_".join(sorted([x.name for x in self.reactants]))
        sp = "_".join(sorted([x.name for x in self.products]))

        return f"{sr}__{sp}"

    def check(self, errors: bool) -> None:
        if not self.check_mass():
            self.logger.warning(f"Mass not conserved in: {self.verbatim}")
            if errors:
                sys.exit(1)

        if not self.check_charge():
            self.logger.warning(f"Charge not conserved in: {self.verbatim}")
            if errors:
                sys.exit(1)

    def check_mass(self) -> bool:
        return (
            np.sum([r.mass for r in self.reactants])
            - np.sum([p.mass for p in self.products])
        ) < 9.1093837e-28

    def check_charge(self) -> bool:
        return (
            np.sum([x.charge for x in self.reactants])
            - np.sum([x.charge for x in self.products])
        ) == 0

    def get_verbatim(self) -> str:
        return (
            f"{' + '.join([x.name for x in self.reactants])}"
            " -> "
            f"{' + '.join([x.name for x in self.products])}"
        )

    def get_latex(self) -> str:
        latex = (
            f"{' + '.join([x.latex for x in self.reactants])}"
            "\\,\\to\\,"
            f"{' + '.join([x.latex for x in self.products])}"
        )
        return f"${latex}$"

    def get_flux_expression(
        self,
        idx: int = 0,
        rate_variable: str = "k",
        species_variable: str = "y",
        brackets: str = "[]",
        idx_prefix: str = "",
    ) -> str:
        if len(brackets) != 2:
            self.logger.error("Brackets must be a string of length 2, e.g. '[]'")
            sys.exit(1)

        lb, rb = brackets[0], brackets[1]
        flux = f"{rate_variable}{lb}{idx}{rb} * " + " * ".join(
            [f"{species_variable}{lb}{idx_prefix + x.fidx}{rb}" for x in self.reactants]
        )

        return flux

    def has_any_species(self, species: list[Specie | str] | str | Specie) -> bool:
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return any([x.name in sp_list for x in self.reactants + self.products])

    def has_reactant(self, species: list[Specie | str] | str | Specie) -> bool:
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return any([x.name in sp_list for x in self.reactants])

    def has_product(self, species: list[Specie | str] | str | Specie) -> bool:
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return any([x.name in sp_list for x in self.products])

    def get_code(self, lang="cpp") -> str:
        """
        Generate code for the reaction rate in the specified language.

        Args:
            lang: Target programming language. Default: "cpp"
                Supported: "python", "c", "cxx", "fortran", "rust", "julia", "r"

        Returns:
            Code string for the reaction rate expression

        Raises:
            ValueError: If the language is not supported
        """
        fmap = {
            "python": pycode,
            "c": ccode,
            "cxx": cxxcode,
            "fortran": fcode,
            "rust": rust_code,
            "julia": julia_code,
            "r": rcode,
        }

        if not fmap.get(lang, ""):
            raise ValueError(
                f"{lang} is not supported. Supported languages are:\n\n{fmap.keys()}"
            )
        if (
            hasattr(self.rate, "func")
            and isinstance(self.rate.func, type(Function("f")))
            and self.rate.func.__name__ == "photorates"
        ):
            # Return a placeholder that will be replaced later
            return (
                f"photorates($IDX$, {', '.join(str(arg) for arg in self.rate.args[1:])})"
            )

        return fmap[lang](self.get_sympy(), strict=False)

    def get_sympy(self) -> Basic:
        return sympify(self.rate)

    def plot(self, ax=None) -> None:
        import matplotlib.pyplot as plt

        tmin = 2.73 if self.tmin is None else self.tmin
        tmax = 1e6 if self.tmax is None else self.tmax

        tgas = np.logspace(np.log10(tmin), np.log10(tmax), 100)
        r = lambdify("tgas", self.rate, "numpy")
        y = np.array([r(t) for t in tgas])

        if ax is None:
            _, ax = plt.subplots()

        ax.plot(tgas, y)
        ax.set_xlabel("Temperature (K)")
        ax.set_ylabel("Rate")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(self.get_latex())
        ax.grid()

        if ax is None:
            plt.show()

    def plot_xsecs(
        self, ax=None, energy_unit="eV", energy_log=True, xsecs_log=True
    ) -> None:
        import matplotlib.pyplot as plt

        if self.xsecs_dict is None:
            self.logger.info(f"No cross sections available for: {self}")
            return

        if ax is None:
            _, ax = plt.subplots()

        clight = constants.cgs.c  # cm/s
        hplanck = constants.cgs.h  # erg s

        if energy_unit == "eV":
            energies = np.array(self.xsecs_dict["energy"]) / 1.60218e-12
            xlabel = "Energy (eV)"
        elif energy_unit == "erg":
            energies = np.array(self.xsecs_dict["energy"])
            xlabel = "Energy (erg)"
        elif energy_unit == "nm":
            energies = clight * hplanck * 1e7 / np.array(self.xsecs_dict["energy"])
            xlabel = "Wavelength (nm)"
        elif energy_unit in ["um", "micron"]:
            energies = clight * hplanck * 1e4 / np.array(self.xsecs_dict["energy"])
            xlabel = "Wavelength (µm)"
        else:
            self.logger.error(f"Unknown energy unit: {energy_unit}")
            sys.exit(1)

        xsecs = np.array(self.xsecs_dict["xsecs"])

        ax.plot(energies, xsecs)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Cross section (cm^2)")
        if energy_log:
            ax.set_xscale("log")
        if xsecs_log:
            ax.set_yscale("log")
        ax.set_title(self.get_latex())
        ax.grid()

        if ax is None:
            plt.show()


class Reactions(Catalogue[Reaction]):
    def __init__(self, reactions: list[Reaction] | None = None):
        _by_name: dict[str, Reaction] | None = None
        _by_serialized: dict[str, Reaction] = {}

        if reactions is not None:
            _by_name = {r.verbatim: r for r in reactions}
            _by_serialized = {r.serialized: r for r in reactions}

        super().__init__(reactions, _by_name)
        self._by_serialized = _by_serialized

    def add(self, reaction: Reaction) -> None:
        if not isinstance(reaction, Reaction):
            raise ValueError(f"'{reaction}' must be an instance of 'Reaction'")

        self._by_name[reaction.verbatim] = reaction
        self._by_serialized[reaction.serialized] = reaction
        self._list.append(reaction)
        self.count = len(self._list)

    def from_serialized(self, serialized: str) -> Reaction:
        return self._by_serialized[serialized]

    def from_verbatim(self, verbatim: str, rtype: str | None = None) -> Reaction | None:
        rea = self._by_name[verbatim]
        if rtype is None or rea.guess_type() == rtype:
            return rea

    def get_list(self):
        return self._list
