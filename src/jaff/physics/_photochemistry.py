from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from ..io import JaffLogger
from . import constants

if TYPE_CHECKING:
    import logging

    from ..core import Reaction


class Photochemistry:
    def __init__(self):
        self.logger: logging.Logger = JaffLogger().get_logger()
        self.xsecs: dict = {}
        self.xsecs_folder: Path = Path(__file__).parent.parent / "data" / "xsecs"

        self.load_xsecs_leiden()

    def load_xsecs_leiden(self) -> None:
        for file in self.xsecs_folder.iterdir():
            if not file.suffix.lower() == ".dat" or "__" not in file.stem:
                continue

            # take last commented line as header, remove #, and split by spaces
            with open(file) as f:
                header = (
                    [x for x in f.readlines() if x.startswith("#")][-1]
                    .lower()
                    .replace("#", "")
                    .strip()
                    .split()
                )
            header = [x for x in header if x != ""]

            # get the name of the file without path and extension, i.e. the reaction name in the form R__P_P

            rrs = file.stem.split("__")[0].split("_")
            pps = file.stem.split("__")[1].split("_")

            rea_serialized = f"{'_'.join(sorted(rrs))}__{'_'.join(sorted(pps))}"

            # count the charges in the reactants and products
            rcharge = np.sum([x.count("+") for x in rrs])
            pcharge = np.sum([x.count("+") for x in pps])

            # determine if the reaction is dissociation or ionization
            mode = "ion" if pcharge > rcharge else "dis"

            # determine the index of the read and wave columns
            iread = iwave = None
            for i, h in enumerate(header):
                if mode in h:
                    iread = i
                if "wave" in h:
                    iwave = i

            if iread is None or iwave is None:
                self.logger.error(f"Could not find read or wave in header of {file}")
                sys.exit(1)

            data = np.loadtxt(file, comments="#").T

            clight = constants.cgs.c  # cm/s
            hplanck = constants.cgs.h  # erg s

            energy = clight * hplanck / (data[iwave].astype(float) * 1e-7)  # nm -> erg
            xs = data[iread].astype(float)  # cm^2

            self.xsecs[rea_serialized] = {"energy": energy, "xsecs": xs}

    # returns a dictionary with keys "energy" and "xsecs"
    # energy in erg, xsecs in cm^2
    def get_xsec(self, reaction: Reaction) -> dict:
        if reaction.serialized not in self.xsecs:
            self.logger.error(
                f"Reaction {reaction.serialized} not found in photochemistry data"
            )
            self.logger.error(
                f"Add the file to {self.xsecs_folder} as {reaction.serialized}"
            )
            sys.exit(1)

        return self.xsecs[reaction.serialized]
