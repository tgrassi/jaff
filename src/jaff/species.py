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
    _ATTRS: frozenset[str] = frozenset(
        {"name", "mass", "exploded", "charge", "index", "fidx", "serialized", "elements"}
    )

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
        self.charge: int = 0
        self.index: int = index
        self.__latex: str = ""
        self.fidx: str = self.get_fidx()
        self.serialized: str = ""

        self.parse(mass_dict)
        self.serialize()

        self.elements: Elements = Elements(self, mass_dict)

    def __repr__(self):
        return f"Species(name={self.name!r}, mass={self.mass!r}, index={self.index!r})"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Specie):
            raise TypeError(
                f"'==' not supported between instances of 'Specie' and '{other}'"
            )

        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if not isinstance(other, Specie):
            raise TypeError(
                f"'<' not supported between instances of 'Specie' and '{other}'"
            )

        return self.name < other.name

    def get_fidx(self) -> str:
        return (
            "idx_e"
            if self.name == "e-"
            else f"idx_{self.name.replace('+', 'j').replace('-', 'k').strip().lower()}"
        )

    def serialize(self) -> str:
        self.serialized = "/".join(sorted(self.exploded))

        return self.serialized

    def latex(self, dollars: bool = False):
        return f"${self.__latex}$" if dollars else self.__latex

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

        self.__latex = f"{{\\rm {latex}}}"

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

    def names(self, ne: bool = False) -> Vector[str]:
        return Vector([s.name for s in self if not (ne and s.name == "e-")])

    def masses(self, ne: bool = False) -> Vector[float | None]:
        return Vector([s.mass for s in self if not (ne and s.name == "e-")])

    def exploded(self, ne: bool = False) -> Vector[list[str]]:
        return Vector([s.exploded for s in self if not (ne and s.name == "e-")])

    def latex(self, dollars: bool = True, ne: bool = False) -> Vector[str]:
        return Vector([s.latex(dollars) for s in self if not (ne and s.name == "e-")])

    def charges(self, ne: bool = False) -> Vector[int]:
        return Vector([s.charge for s in self if not (ne and s.name == "e-")])

    def serialized(self, ne: bool = False) -> Vector[str]:
        return Vector([s.serialized for s in self if not (ne and s.name == "e-")])

    def elements(self, ne: bool = False) -> Vector[Elements]:
        return Vector([s.elements for s in self if not (ne and s.name == "e-")])

    def e_idx(self) -> int | None:
        if "e-" in self:
            return self["e-"].index

    def normalized_names(self) -> Vector[str]:
        return Vector([s.name.lower().replace("+", "p").replace("-", "n") for s in self])

    def neutral(self, attr: str = "") -> Vector[Specie | int]:
        if attr:
            if attr not in Specie._ATTRS:
                raise ValueError(f"Invalid attribute passed: {attr}")

            return Vector([getattr(s, attr) for s in self if s.charge == 0])

        return Vector([s for s in self if s.charge == 0])

    def charged(
        self, attr: str = "", mass: bool = False, ne: bool = False
    ) -> Vector[Specie]:
        if attr:
            if attr not in Specie._ATTRS:
                raise ValueError(f"Invalid attribute passed: {attr}")

            return Vector(
                [
                    getattr(s, attr)
                    for s in self
                    if s.charge != 0 and not (ne and s.name == "e-")
                ]
            )

        return Vector([s for s in self if s.charge != 0 and not (ne and s.name == "e-")])

    def charge_truths(self, ne: bool = False) -> Vector[int]:
        return Vector([int(bool(s.charge)) for s in self if not (ne and s.name == "e-")])
