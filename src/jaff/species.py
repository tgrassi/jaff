from __future__ import annotations

import sys
from itertools import product
from typing import TYPE_CHECKING

from .common.helper import ElementProps
from .core.logger import JaffLogger
from .elements import Elements
from .types import Catalogue, Vector

if TYPE_CHECKING:
    import logging


class Specie:
    def __init__(self, name: str, mass_dict: dict[str, ElementProps], index: int):
        self.logger: logging.Logger = JaffLogger().get_logger()
        if name.lower() in ["e", "eletron", "electrons", "el", "els"] or name in [
            "E",
            "E-",
        ]:
            self.logger.error(f"Electrons found with name: {name}. Use e- instead")
            sys.exit(1)

        self.name: str = name
        self.mass: float | None = None
        self.exploded: list[str] = []
        self.latex: str = ""
        self.charge: int = 0
        self.index: int = index
        self.fidx: str = self.get_fidx()
        self.serialized: str = ""

        self.parse(mass_dict)
        self.serialize()

        self.elements: Elements = Elements(self, mass_dict)

    def __repr__(self):
        return f"Species(name={self.name!r}, mass={self.mass!r}, index={self.index!r})"

    def __str__(self):
        return self.name

    def get_fidx(self) -> str:
        return (
            "idx_e"
            if self.name == "e-"
            else f"idx_{self.name.replace('+', 'j').replace('-', 'k').strip().lower()}"
        )

    def serialize(self) -> str:
        self.serialized = "/".join(sorted(self.exploded))

        return self.serialized

    def parse(self, mass_dict: dict) -> None:
        atoms = sorted(mass_dict.keys(), key=lambda x: len(x), reverse=True)
        ps = ["".join(x) for x in product("qzxj", repeat=4)][: len(atoms)]
        proxy = {a: p for a, p in zip(atoms, ps)}
        proxy_rev = {p: a for a, p in proxy.items()}

        pname = self.name.strip()
        for a in atoms:
            pname = pname.replace(a, f"${proxy[a]}$")

        def is_number(s: str) -> bool:
            if s == "x":
                return True
            try:
                float(s)
                return True
            except ValueError:
                return False

        alist = [x for x in pname.split("$") if x != ""]
        expl = []
        pold = None
        for p in alist:
            if not is_number(p):
                expl += [p]
            else:
                if p != "x":
                    expl += [pold] * max(int(p) - 1, 1)
            pold = p
        self.exploded = sorted([proxy_rev[x] for x in expl])
        self.mass = sum([mass_dict[x]["mass"] for x in self.exploded])

        # latex name
        latex = self.name.strip()
        for i in range(0, 10):
            latex = latex.replace(str(i), "_{" + str(i) + "}")
        latex = latex.replace("+", "^{+}")
        latex = latex.replace("-", "^{-}")
        if "_ORTHO" in latex:
            latex = "o" + latex.replace("_ORTHO", "")
        if "_PARA" in latex:
            latex = "p" + latex.replace("_PARA", "")
        if "_META" in latex:
            latex = "m" + latex.replace("_META", "")
        if "_DUST" in latex:
            latex = latex.replace("_DUST", "") + "ice"

        latex = latex.replace("GRAIN", "g")

        self.latex = f"{{\\rm {latex}}}"

        # charge
        if self.name == "e-":
            self.charge = -1
            return

        self.charge = 0
        name = self.name
        # charge symbol only at the end of the name
        while name.endswith("+") or name.endswith("-"):
            if name.endswith("+"):
                self.charge += 1
            elif name.endswith("-"):
                self.charge -= 1
            name = name[:-1]
        # self.charge = self.name.count("+") - self.name.count("-")


class Species(Catalogue[Specie]):
    def __init__(self, species: list[Specie] | None = None):
        _by_name: dict[str, Specie] | None = None
        _by_serialized: dict[str, Specie] = {}

        if species is not None:
            _by_name = {sp.name: sp for sp in species}
            _by_serialized = {sp.serialized: sp for sp in species}

        super().__init__(species, _by_name)
        self._by_serialized = _by_serialized

    def add(self, specie: Specie) -> None:
        if not isinstance(specie, Specie):
            raise ValueError(f"'{specie}' must be an instance of 'Specie'")

        if specie.name not in self._by_name:
            self._by_name[specie.name] = specie
            self._by_serialized[specie.serialized] = specie
            self._list.append(specie)
            self.count = len(self._list)

    def from_serialized(self, serialized: str) -> Specie:
        return self._by_serialized[serialized]

    def from_name(self, name: str) -> Specie:
        return self._by_name[name]

    def get_list(self) -> list[Specie]:
        return self._list

    def names(self) -> Vector[str]:
        return Vector([s.name for s in self])

    def masses(self) -> Vector[float | None]:
        return Vector([s.mass for s in self])

    def exploded(self) -> Vector[list[str]]:
        return Vector([s.exploded for s in self])

    def latex(self) -> Vector[str]:
        return Vector([s.latex for s in self])

    def charges(self) -> Vector[int]:
        return Vector([s.charge for s in self])

    def serialized(self) -> Vector[str]:
        return Vector([s.serialized for s in self])

    def elements(self) -> Vector[Elements]:
        return Vector([s.elements for s in self])

    def e_idx(self) -> int:
        return self["e-"].index

    def normalized_names(self) -> Vector[str]:
        return Vector([s.name.lower().replace("+", "p").replace("-", "n") for s in self])

    def neutral(self) -> Vector[Specie]:
        return Vector([s for s in self if s.charge == 0])

    def charged(self) -> Vector[Specie]:
        return Vector([s for s in self if s.charge != 0])

    def neutral_indies(self) -> Vector[int]:
        return Vector([i for i, s in enumerate(self) if s.charge == 0])

    def charged_indies(self) -> Vector[int]:
        return Vector([i for i, s in enumerate(self) if s.charge != 0])

    def charge_truths(self) -> Vector[int]:
        return Vector([int(bool(s.charge)) for s in self])

    def masses_ne(self) -> Vector[float | None]:
        return Vector([s.mass for s in self if str(s) != "e-"])

    def charges_ne(self) -> Vector[int]:
        return Vector([s.charge for s in self if str(s) != "e-"])

    def charge_truths_ne(self) -> Vector[int]:
        return Vector([int(bool(s.charge)) for s in self if str(s) != "e-"])

    def neutral_indices(self) -> Vector[int]:
        return Vector([s.index for s in self if s.charge == 0])

    def charged_indices(self) -> Vector[int]:
        return Vector([s.index for s in self if s.charge != 0])

    def neutral_indices_ne(self) -> Vector[int]:
        return Vector([s.index for s in self if s.charge == 0 and str(s) != "e-"])

    def charged_indices_ne(self) -> Vector[int]:
        return Vector([s.index for s in self if s.charge != 0 and str(s) != "e-"])

    def neutral_masses(self) -> Vector[float | None]:
        return Vector([s.mass for s in self if s.charge == 0])

    def charged_masses(self) -> Vector[float | None]:
        return Vector([s.mass for s in self if s.charge != 0])

    def neutral_masses_ne(self) -> Vector[float | None]:
        return Vector([s.mass for s in self if s.charge == 0 and str(s) != "e-"])

    def charged_masses_ne(self) -> Vector[float | None]:
        return Vector([s.mass for s in self if s.charge != 0 and str(s) != "e-"])

    def charged_charges(self) -> Vector[int]:
        return Vector([s.charge for s in self if s.charge != 0])

    def charged_charges_ne(self) -> Vector[int]:
        return Vector([s.charge for s in self if s.charge != 0 and str(s) != "e-"])
