from __future__ import annotations

import sys
from itertools import product
from typing import TYPE_CHECKING

from .core.logger import JaffLogger

if TYPE_CHECKING:
    import logging


class Species:
    def __init__(self, name: str, mass_dict: dict, index: int):
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
