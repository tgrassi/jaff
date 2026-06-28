"""Collapse the per-species line-shielding tables into a single HDF5 file.

``line_shielding_functions/<species>/<channel>_<radfield>`` holds the Leiden
shielding functions (https://home.strw.leidenuniv.nl/~ewine/photo/), one plain
text table per species, photo-channel and radiation field.  This utility merges
them into ``data/shielding/leiden.hdf5`` with **one group per reaction**, keyed
exactly like ``data/xsecs/leiden.hdf5`` (e.g. ``"CO__C_O"``).

Schema
------
Root attrs: ``database`` ("leiden"), ``description``, ``created``.

::

    <reaction_key>/
        attrs: reactants, products, cross_section ("photodissociation" |
               "photoionisation")
        N                         dataset (cm^-2), shared by all radfields
        <radfield>/               e.g. "ISRF", "Ly-alpha", "bb-10000"
            attrs: radiation_field, and (HF only) wavelength_begin/end/step
                   (nm), unshielded_rate (s^-1)
            <species>             one shielding-factor dataset per source
                                  column (H2, H, self, C, N2, CO, ... or the
                                  Zn variant H2, H, dust, self, combined)

Reaction keys
-------------
The ``N`` (column-density) grid is identical across a reaction's radfields, so
it is stored once at group level (verified equal, else the build aborts).
Columns that are entirely NaN (some ``*_Lyalpha`` tables) are omitted.

- **photodissociation** -> the Leiden reaction whose sole reactant is the
  species (a dissociation channel, e.g. ``CO__C_O``).
- **photoionisation** -> the Leiden reaction if Leiden keyed that species by its
  ionisation channel (e.g. ``Al__Al+_e-``, ``Ca+__Ca++_e-``, ``H-__H_e-``);
  otherwise the key is constructed as ``"<X>__<X+>_e-"`` (neutral ``X`` -> ``X+``,
  cation ``X+`` -> ``X++``, anion ``X-`` -> neutral ``X``).

Values are copied verbatim from the source tables -- no numerical transform.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import h5py
import numpy as np

from jaff.io import JaffLogger

_STR_DT = h5py.string_dtype(encoding="utf-8")

#: Lossless dataset compression (gzip level 4 + chunking), matching the
#: ``collapse_xsecs_hdf5`` convention.
COMPRESSION_KW: dict = {"compression": "gzip", "compression_opts": 4, "chunks": True}

#: Source radfield token -> output subgroup/attr name.  Blackbody temperatures
#: become ``bb-<T>``; year-suffixed parametrizations get a hyphen; ``Lyalpha``
#: becomes ``Ly-alpha``.  Unlisted fields (ISRF, solar, TW-Hya) are unchanged.
_RADFIELD_RENAME: dict[str, str] = {
    "4000K": "bb-4000",
    "10000K": "bb-10000",
    "20000K": "bb-20000",
    "Lyalpha": "Ly-alpha",
    "mathis1983": "mathis-1983",
    "habing1968": "habing-1968",
    "gondhalekar1980": "gondhalekar-1980",
}

#: HF tables carry extra ``# key: value`` provenance lines -> radfield attrs.
_HF_META_KEYS: dict[str, str] = {
    "wavelength_begin (nm)": "wavelength_begin",
    "wavelength_end (nm)": "wavelength_end",
    "wavelength_step (nm)": "wavelength_step",
    "unshielded_rate (s-1)": "unshielded_rate",
}


def _ionize(species: str) -> str:
    """Singly-ionise a species name: ``X`` -> ``X+``, ``X+`` -> ``X++``,
    anion ``X-`` -> neutral ``X`` (photodetachment)."""
    if species.endswith("-"):
        return species[:-1]
    return species + "+"


def _load_leiden_map(leiden_h5: Path) -> dict[str, dict]:
    """Map each single-reactant species to its Leiden reaction key/products."""
    out: dict[str, dict] = {}
    with h5py.File(leiden_h5, "r") as f:
        for key, grp in f.items():
            reactants = [r.decode() if isinstance(r, bytes) else str(r)
                         for r in grp.attrs["reactants"]]
            products = [p.decode() if isinstance(p, bytes) else str(p)
                        for p in grp.attrs["products"]]
            if len(reactants) == 1:
                out[reactants[0]] = {
                    "key": key,
                    "reactants": reactants,
                    "products": products,
                    "is_ionisation": "e-" in products,
                }
    return out


def _resolve_reaction(
    species: str, channel: str, leiden_map: dict[str, dict]
) -> tuple[str, list[str], list[str]]:
    """Return ``(reaction_key, reactants, products)`` for a species + channel."""
    entry = leiden_map.get(species)
    if channel == "photodissociation":
        if entry is None or entry["is_ionisation"]:
            raise ValueError(
                f"no Leiden dissociation reaction for {species!r} "
                f"(Leiden entry: {entry['key'] if entry else None})"
            )
        return entry["key"], entry["reactants"], entry["products"]

    # photoionisation
    if entry is not None and entry["is_ionisation"]:
        return entry["key"], entry["reactants"], entry["products"]
    ion = _ionize(species)
    return (
        f"{'.'.join(sorted([species, '_PHOTON']))}__{ion}.e-",
        sorted([species, "_PHOTON"]),
        [ion, "e-"],
    )


def _parse_table(path: Path) -> tuple[list[str], np.ndarray, dict]:
    """Parse one shielding file -> ``(column_names, data, hf_meta)``.

    ``column_names[0]`` is ``"N"``; the rest are shielding species.  ``data`` is
    shaped ``(n_rows, n_cols)``.  ``hf_meta`` holds any HF provenance attrs.
    """
    lines = path.read_text().splitlines()
    hf_meta: dict = {}
    header: str | None = None
    for ln in lines:
        if ln.lstrip().startswith("#"):
            body = ln.lstrip().lstrip("#").strip()
            # the column header is the last comment line before the data
            if body.split()[:1] == ["N"]:
                header = body
            for raw_key, attr in _HF_META_KEYS.items():
                if body.startswith(raw_key):
                    hf_meta[attr] = float(body.split(":", 1)[1])
    if header is None:
        raise ValueError(f"no column header found in {path}")
    columns = header.split()

    data = np.genfromtxt(path, comments="#")
    if data.shape[1] != len(columns):
        raise ValueError(
            f"{path}: header has {len(columns)} columns but data has "
            f"{data.shape[1]}"
        )
    return columns, data, hf_meta


def build_shielding(src_dir: Path, leiden_h5: Path, out_path: Path, logger) -> int:
    """Merge the per-species shielding tables into a single HDF5 file."""
    leiden_map = _load_leiden_map(leiden_h5)

    # reaction_key -> {reactants, products, cross_section, radfields:{name:{N,cols,meta}}}
    reactions: dict[str, dict] = {}
    n_files = 0
    for species_dir in sorted(p for p in src_dir.iterdir() if p.is_dir()):
        species = species_dir.name
        for f in sorted(species_dir.iterdir()):
            channel, _, radfield = f.name.partition("_")
            radfield = _RADFIELD_RENAME.get(radfield, radfield)
            key, reactants, products = _resolve_reaction(species, channel, leiden_map)
            columns, data, hf_meta = _parse_table(f)

            cols = {
                name: data[:, i]
                for i, name in enumerate(columns[1:], start=1)
                if not np.isnan(data[:, i]).all()  # drop all-NaN columns
            }
            entry = reactions.setdefault(
                key,
                {
                    "reactants": reactants,
                    "products": products,
                    "cross_section": channel,
                    "radfields": {},
                },
            )
            if radfield in entry["radfields"]:
                raise ValueError(f"duplicate {radfield!r} for reaction {key!r}")
            entry["radfields"][radfield] = {
                "N": data[:, 0],
                "cols": cols,
                "meta": hf_meta,
            }
            n_files += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(out_path, "w") as h5:
        h5.attrs["database"] = "leiden"
        h5.attrs["description"] = (
            "Leiden line-shielding functions, one group per reaction (keyed as in "
            "xsecs/leiden.hdf5); shielding factors are dimensionless, column "
            "density N in cm^-2."
        )
        h5.attrs["created"] = date.today().isoformat()

        for key in sorted(reactions):
            entry = reactions[key]
            grp = h5.create_group(key)
            grp.attrs["reactants"] = np.array(entry["reactants"], dtype=_STR_DT)
            grp.attrs["products"] = np.array(entry["products"], dtype=_STR_DT)
            grp.attrs["cross_section"] = entry["cross_section"]

            radfields = entry["radfields"]
            # N is shared across radfields -> verify identical, store once.
            ref_N = next(iter(radfields.values()))["N"]
            for name, rf in radfields.items():
                if not np.array_equal(rf["N"], ref_N):
                    raise ValueError(
                        f"reaction {key!r}: radfield {name!r} has a different N grid"
                    )
            n_ds = grp.create_dataset("N", data=ref_N, **COMPRESSION_KW)
            n_ds.attrs["unit"] = "cm-2"

            for radfield in sorted(radfields):
                rf = radfields[radfield]
                rgrp = grp.create_group(radfield)
                rgrp.attrs["radiation_field"] = radfield
                for attr, val in rf["meta"].items():
                    rgrp.attrs[attr] = val
                for name, arr in rf["cols"].items():
                    rgrp.create_dataset(name, data=arr, **COMPRESSION_KW)

    logger.info(
        f"Wrote {len(reactions)} reactions ({n_files} source files) to {out_path}"
    )
    return len(reactions)


def main() -> None:
    """Build ``data/shielding/leiden.hdf5`` from ``line_shielding_functions/``."""
    logger = JaffLogger().get_logger()
    repo = Path(__file__).parent.parent.parent.parent
    src_dir = repo / "line_shielding_functions"
    leiden_h5 = Path(__file__).parent.parent / "data" / "xsecs" / "leiden.hdf5"
    out_path = Path(__file__).parent.parent / "data" / "shielding" / "leiden.hdf5"
    build_shielding(src_dir, leiden_h5, out_path, logger)


if __name__ == "__main__":
    main()
