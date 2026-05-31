"""
Loader for the Leiden photodissociation / photoionisation cross section database.

This module provides the :class:`Photochemistry` class, which reads ``.dat``
files from the Leiden Observatory photodissociation-region (PDR) database and
exposes per-reaction cross sections as (energy, cross-section) arrays.

File-naming convention (Leiden format)
---------------------------------------
Each ``.dat`` file in the ``data/xsecs/`` folder is named::

    R1_R2__P1_P2.dat

where ``R1``, ``R2`` are reactant species names (separated by ``_``) and
``P1``, ``P2`` are product species names.  The double underscore ``__``
separates reactants from products.

The last ``#``-prefixed comment line in each file is treated as the column
header.  Two column names are required:

- A column whose name contains ``"wave"`` -- wavelength in nanometres (nm).
- A column whose name contains ``"ion"`` (photoionisation) or ``"dis"``
  (photodissociation), selected based on the charge balance of the reaction.

Energy conversion
-----------------
Wavelength values (nm) from the data files are converted to photon energies
in erg using::

    E = h * c / λ    (with λ in cm, h in erg·s, c in cm/s)

i.e. ``E [erg] = h * c / (λ_nm * 1e-7)`` (1 nm = 1e-7 cm).

References
----------
van Dishoeck, E. F. et al., Leiden Observatory PDR database.
"""

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
    """
    Load and cache photoionisation/photodissociation cross sections from the Leiden database.

    On construction the class scans the ``data/xsecs/`` directory (relative to
    the JAFF package root) for all ``.dat`` files whose stem contains ``"__"``,
    loads each file, determines the reaction mode (ionisation vs.
    dissociation), converts wavelengths to photon energies in erg, and stores
    the result in :attr:`xsecs`.

    Attributes
    ----------
    logger : logging.Logger
        Logger instance for warning/error messages.
    xsecs : dict
        Mapping from *serialised reaction key* (``"R1_R2__P1_P2"`` with sorted
        species names) to a dict with keys:

        - ``"energy"`` : numpy.ndarray -- photon energies in erg, sorted in
          ascending wavelength order (i.e. *descending* energy order as stored
          in the file).
        - ``"xsecs"`` : numpy.ndarray -- cross sections in cm².

    xsecs_folder : pathlib.Path
        Absolute path to the directory containing the ``.dat`` files.
    """

    def __init__(self):
        """Scan and load all Leiden cross-section ``.dat`` files on construction.

        Cross sections are stored in :attr:`xsecs` keyed by the serialised
        reaction string.  The ``xsecs_folder`` is resolved relative to the
        JAFF package directory.
        """
        self.logger: logging.Logger = JaffLogger().get_logger()
        self.xsecs: dict = {}
        # Resolve the cross-section data directory relative to this source file.
        self.xsecs_folder: Path = Path(__file__).parent.parent / "data" / "xsecs"

        self.load_xsecs_leiden()

    def load_xsecs_leiden(self) -> None:
        """
        Scan ``xsecs_folder`` and load all Leiden-format cross section files.

        For each valid ``.dat`` file the method:

        1. Reads the last ``#``-prefixed header line to locate the wavelength
           and cross-section columns.
        2. Determines the reaction mode (``"ion"`` or ``"dis"``) from the
           charge balance of reactants vs. products.
        3. Loads the numeric data, converts wavelengths from nm to photon
           energies in erg, and stores the result in :attr:`xsecs`.

        Returns
        -------
        None
            Results are stored in ``self.xsecs`` in-place.

        Notes
        -----
        Files without a ``__`` separator in their stem (i.e. not following the
        Leiden naming convention) are silently skipped.

        If the header line cannot be parsed (missing ``"wave"`` or cross-section
        column), the method logs an error and exits with a non-zero status code.
        """
        for file in self.xsecs_folder.iterdir():
            # Skip non-.dat files and files not following the R__P naming scheme.
            if not file.suffix.lower() == ".dat" or "__" not in file.stem:
                continue

            # The last comment line is used as the column-header row.
            with open(file) as f:
                header = (
                    [x for x in f.readlines() if x.startswith("#")][-1]
                    .lower()
                    .replace("#", "")
                    .strip()
                    .split()
                )
            header = [x for x in header if x != ""]

            # Parse reactant and product species names from the file stem.
            # File stem format: "R1_R2__P1_P2"  (double underscore as delimiter)
            rrs = file.stem.split("__")[0].split("_")
            pps = file.stem.split("__")[1].split("_")

            # Build a canonical reaction key with species sorted alphabetically
            # within each side so that look-ups are order-independent.
            rea_serialized = f"{'_'.join(sorted(rrs))}__{'_'.join(sorted(pps))}"

            # Determine reaction mode from charge balance:
            # count "+" in species names as a proxy for ionic charge.
            rcharge = np.sum([x.count("+") for x in rrs])
            pcharge = np.sum([x.count("+") for x in pps])
            # If the product side carries more charge, a free electron was
            # released → photoionisation; otherwise → photodissociation.
            mode = "ion" if pcharge > rcharge else "dis"

            # Locate the wavelength column and the relevant cross-section column.
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

            # CGS constants for energy conversion.
            clight = constants.cgs.c  # cm/s
            hplanck = constants.cgs.h  # erg·s

            # Convert wavelength from nm to photon energy in erg:
            #   E = h·c / λ  with λ in cm (1 nm = 1e-7 cm)
            energy = clight * hplanck / (data[iwave].astype(float) * 1e-7)  # erg
            xs = data[iread].astype(float)  # cm²

            self.xsecs[rea_serialized] = {"energy": energy, "xsecs": xs}

    def get_xsec(self, reaction: Reaction) -> dict:
        """
        Return the cross section data for a single reaction.

        Parameters
        ----------
        reaction : Reaction
            The photochemical reaction whose cross section is requested.
            ``reaction.serialized`` must match a key in :attr:`xsecs`.

        Returns
        -------
        dict
            Dictionary with keys:

            - ``"energy"`` : numpy.ndarray -- photon energies in erg.
            - ``"xsecs"`` : numpy.ndarray -- cross sections in cm².

        Raises
        ------
        SystemExit
            If the reaction's serialised key is not found in :attr:`xsecs`.
            A descriptive error message (including the expected file path) is
            logged before exiting.
        """
        if reaction.serialized not in self.xsecs:
            self.logger.error(
                f"Reaction {reaction.serialized} not found in photochemistry data"
            )
            self.logger.error(
                f"Add the file to {self.xsecs_folder} as {reaction.serialized}"
            )
            sys.exit(1)

        return self.xsecs[reaction.serialized]
