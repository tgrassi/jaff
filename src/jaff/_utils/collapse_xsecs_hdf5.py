"""Collapse the per-reaction cross-section files into two combined HDF5 files.

The Leiden (``data/xsecs/leiden/*.h5``) and NORAD/OP (``data/xsecs/op/*.dat``)
folders each hold one file per reaction.  This utility merges each folder into a
single HDF5 file -- ``data/xsecs/leiden.h5`` and ``data/xsecs/op.h5`` -- with one
group per reaction (group name = the serialized stem, e.g. ``"CH__C_H"``).

Schema
------
Root attrs: ``database`` ("leiden"/"norad"), ``description``, ``created``.

Each group has datasets, all co-sorted by **ascending photon energy**:

- ``photon_energy``   -- eV   (Leiden wavelengths in nm are converted via
  ``E = h c / lambda``).
- ``photoabsorption`` / ``photodissociation`` / ``photoionization`` -- cm^2.
  Leiden groups carry all three; NORAD groups carry only ``photoionization``.

Every dataset has a ``unit`` attr ("eV" or "cm2").

Group attrs:

- ``reactants`` / ``products`` -- string lists parsed from the serialized stem.
- NORAD groups additionally: ``Z``, ``n_electrons``, ``charge``,
  ``accuracy_variant``, ``data_format``, ``source_url`` (from the ``.dat``
  ``#`` header).

Excluded: ``cross_section_properties.csv``, the per-file ``README``, the stray
``HI.dat``/``HeI.dat`` spectroscopic-name files, and ``op/raw/``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import h5py
import numpy as np

from jaff.io import JaffLogger
from jaff.physics import constants

#: eV per erg (1 eV = 1.602176634e-12 erg).
EV_PER_ERG: float = 1.0 / 1.602176634e-12
#: cm per nm.
CM_PER_NM: float = 1e-7

#: Leiden source dataset name (British spelling) -> output name.
LEIDEN_XSEC_DATASETS: dict[str, str] = {
    "photoabsorption": "photoabsorption",
    "photodissociation": "photodissociation",
    "photoionisation": "photoionization",
}

_STR_DT = h5py.string_dtype(encoding="utf-8")

#: Lossless dataset compression (gzip level 4 + chunking). ~45% smaller files;
#: decompression is cheap per small reaction, costlier only for the few very
#: large datasets (read once and cache).
COMPRESSION_KW: dict = {"compression": "gzip", "compression_opts": 4, "chunks": True}


def split_reaction(stem: str) -> tuple[list[str], list[str]]:
    """Split a serialized stem into ``(reactants, products)`` string lists.

    ``"CH__C_H"`` -> ``(["CH"], ["C", "H"])``.
    """
    react, _, prod = stem.partition("__")
    return react.split("_"), prod.split("_")


def wavelength_nm_to_eV(wavelength_nm: np.ndarray) -> np.ndarray:
    """Convert wavelength (nm) to photon energy (eV) via ``E = h c / lambda``."""
    lam_cm = wavelength_nm * CM_PER_NM
    energy_erg = constants.cgs.h * constants.cgs.c / lam_cm
    return energy_erg * EV_PER_ERG


def collapse_leiden(leiden_dir: Path, out_path: Path, logger) -> int:
    """Merge all Leiden per-reaction ``.h5`` files into a single HDF5 file."""
    files = sorted(leiden_dir.glob("*.h5"))
    with h5py.File(out_path, "w") as h5:
        h5.attrs["database"] = "leiden"
        h5.attrs["description"] = (
            "Leiden photodissociation/ionisation cross sections, one group per "
            "reaction; photon_energy in eV, cross sections in cm^2."
        )
        h5.attrs["created"] = date.today().isoformat()

        for f in files:
            stem = f.stem
            with h5py.File(f, "r") as src:
                wavelength = src["wavelength"][:].astype(float)
                energy_ev = wavelength_nm_to_eV(wavelength)
                order = np.argsort(energy_ev)  # ascending energy

                grp = h5.create_group(stem)
                reactants, products = split_reaction(stem)
                grp.attrs["reactants"] = np.array(reactants, dtype=_STR_DT)
                grp.attrs["products"] = np.array(products, dtype=_STR_DT)

                e_ds = grp.create_dataset(
                    "photon_energy", data=energy_ev[order], **COMPRESSION_KW
                )
                e_ds.attrs["unit"] = "eV"
                for src_name, out_name in LEIDEN_XSEC_DATASETS.items():
                    if src_name not in src:
                        continue
                    xs = src[src_name][:].astype(float)[order]
                    ds = grp.create_dataset(out_name, data=xs, **COMPRESSION_KW)
                    ds.attrs["unit"] = "cm2"
    logger.info(f"Wrote {len(files)} Leiden groups to {out_path}")
    return len(files)


def _parse_op_header(lines: list[str]) -> dict:
    """Extract NORAD provenance attrs from the ``#`` header of a ``.dat`` file."""
    attrs: dict = {}
    for ln in lines:
        if ln.startswith("# source:"):
            attrs["source_url"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("# variant="):
            for tok in ln[1:].split():
                key, _, val = tok.partition("=")
                if key in ("variant", "format", "Z", "NE", "charge"):
                    attrs[key] = val
    return attrs


def collapse_op(op_dir: Path, out_path: Path, logger) -> int:
    """Merge all NORAD/OP per-reaction serialized ``.dat`` files into one HDF5."""
    files = sorted(p for p in op_dir.glob("*.dat") if "__" in p.stem)
    with h5py.File(out_path, "w") as h5:
        h5.attrs["database"] = "norad"
        h5.attrs["description"] = (
            "NORAD (Nahar/OSU) ground-state photoionisation cross sections, one "
            "group per ion; photon_energy in eV, cross section in cm^2."
        )
        h5.attrs["created"] = date.today().isoformat()

        for f in files:
            stem = f.stem
            lines = f.read_text().splitlines()
            hdr = _parse_op_header([ln for ln in lines if ln.startswith("#")])
            data = np.loadtxt(f, comments="#")
            energy_ev, xsec_cm2 = data[:, 0], data[:, 1]
            order = np.argsort(energy_ev)  # ascending energy

            grp = h5.create_group(stem)
            reactants, products = split_reaction(stem)
            grp.attrs["reactants"] = np.array(reactants, dtype=_STR_DT)
            grp.attrs["products"] = np.array(products, dtype=_STR_DT)
            if "Z" in hdr:
                grp.attrs["Z"] = int(hdr["Z"])
                grp.attrs["n_electrons"] = int(hdr["NE"])
                grp.attrs["charge"] = int(hdr["charge"])
                grp.attrs["accuracy_variant"] = hdr["variant"]
                grp.attrs["data_format"] = hdr["format"]
                grp.attrs["source_url"] = hdr.get("source_url", "")

            e_ds = grp.create_dataset(
                "photon_energy", data=energy_ev[order], **COMPRESSION_KW
            )
            e_ds.attrs["unit"] = "eV"
            x_ds = grp.create_dataset(
                "photoionization", data=xsec_cm2[order], **COMPRESSION_KW
            )
            x_ds.attrs["unit"] = "cm2"
    logger.info(f"Wrote {len(files)} NORAD groups to {out_path}")
    return len(files)


def main() -> None:
    """Build ``leiden.h5`` and ``op.h5`` in ``data/xsecs/``."""
    logger = JaffLogger().get_logger()
    xsecs = Path(__file__).parent.parent / "data" / "xsecs"
    collapse_leiden(xsecs / "leiden", xsecs / "leiden.h5", logger)
    collapse_op(xsecs / "op", xsecs / "op.h5", logger)


if __name__ == "__main__":
    main()
