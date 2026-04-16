from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

import numpy as np
from sympy import Basic, Symbol, __version__
from sympy.core.function import AppliedUndef

from jaff.common.helper import load_mass_dict

from .. import __version__ as jaff_version
from ..common import SCHEMA_VERSION as SYMPY_SCHEMA
from ..common import from_jsonable as sympy_from_jsonable
from ..common import is_jaff_file
from ..common import to_jsonable as sympy_to_jsonable
from ..errors import NotJaffFileError

if TYPE_CHECKING:
    from .. import Network, Species
else:
    Species = "Species"
    Network = "Network"

ReactionProps = TypedDict(
    "ReactionProps",
    {
        "reactants": list["Species"],
        "products": list["Species"],
        "rate": Basic,
        "dE": Basic,
        "dRad_dt": Basic,
        "custom_rad_rate": bool,
        "tmin": float | None,
        "tmax": float | None,
        "original_string": str,
        "xsecs_dict": dict[str, float],
    },
)


JaffProps = TypedDict(
    "JaffProps",
    {
        "file_name": NotRequired[Path],
        "label": NotRequired[str],
        "species": NotRequired[list["Species"]],
        "species_dict": NotRequired[dict[str, int]],
        "reactions": NotRequired[list[ReactionProps]],
    },
)


def to_jaff_file(filename: str | Path, net: "Network"):
    """
    Serialize this Network to a .jaff file (gzip-compressed JSON payload).

    Notes:
        - Uses a versioned, whitelisted SymPy JSON AST for expressions.
        - Excludes photochemistry-specific runtime state; reactions may still
            include xsecs if present.
        - Files are written with gzip compression even when the filename ends
            with `.jaff` (no `.gz` suffix).
    """
    if isinstance(filename, str):
        filename = Path(filename)

    if not is_jaff_file(filename):
        filename = filename.with_suffix(".jaff")

    def has_undefined_functions(expr):
        if not isinstance(expr, Basic):
            return False

        if expr.atoms(AppliedUndef):
            return True

        return False

    def encode_maybe_sympy(value):
        if isinstance(value, str):
            return {"kind": "string", "value": value}
        if isinstance(value, Basic):
            if has_undefined_functions(value):
                raise ValueError(
                    "Cannot serialize: expression contains undefined SymPy function(s)"
                )
            return sympy_to_jsonable(value, include_assumptions=False)
        if value is None:
            return None

        raise TypeError(f"Unsupported value type for serialization: {type(value)!r}")

    def jsonable(obj):
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, dict):
            return {str(k): jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [jsonable(v) for v in obj]
        return obj

    payload = {
        "format": "jaff.network_json",
        "schema_version": 1,
        "jaff_version": jaff_version,
        "sympy_schema_version": SYMPY_SCHEMA,
        "sympy_version": __version__,
        "label": net.label,
        "file_name": net.file_name,
        "species": [
            {
                "name": sp.name,
                "index": int(sp.index),
                "mass": float(sp.mass) if sp.mass is not None else None,
                "charge": int(sp.charge) if sp.charge is not None else None,
            }
            for sp in net.species
        ],
        "rate_symbols": [
            {
                "name": sym.name,
                "assumptions": {
                    k: v
                    for k, v in (sym.assumptions0 or {}).items()
                    if isinstance(k, str) and isinstance(v, bool)
                },
            }
            for sym in sorted(
                {
                    s
                    for r in net.reactions
                    if isinstance(r.rate, Basic)
                    for s in r.rate.free_symbols
                },
                key=lambda s: s.name,
            )
        ],
        "reactions": [
            {
                "reactants": [int(s.index) for s in r.reactants],
                "products": [int(s.index) for s in r.products],
                "rate": encode_maybe_sympy(r.rate),
                "tmin": r.tmin,
                "tmax": r.tmax,
                "dE": encode_maybe_sympy(r.dE),
                "dRad_dt": encode_maybe_sympy(r.dRad_dt),
                "custom_rad_rate": r.custom_rad_rate,
                "original_string": r.original_string,
                "xsecs": jsonable(r.xsecs_dict),
            }
            for r in net.reactions
        ],
    }

    with gzip.open(filename, "wt", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def from_jaff_file(filename: str | Path, errors=False):
    """
    Deserialize a Network previously written by Network.to_jaff_file.

    Parameters:
        filename : str
            `.jaff` file to read (gzip-compressed JSON by default; legacy
            uncompressed JSON is also supported).
        errors : bool
            If True, run Network validation checks and exit on errors.
    """
    from .. import Species

    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(
            f"Invalid network file supplied: {filename}\n"
            "File not found in local file system"
        )

    if not is_jaff_file(filename):
        raise NotJaffFileError("Supplied file is not a jaff network file", filename)

    # Prefer gzip if the filename indicates it; otherwise, sniff the magic header
    # so we can transparently read both compressed and legacy uncompressed files.
    use_gzip = filename.suffix == ".gz"
    if not use_gzip:
        with open(filename, "rb") as fb:
            use_gzip = fb.read(2) == b"\x1f\x8b"

    opener = gzip.open if use_gzip else open
    with opener(filename, "rt", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or payload.get("format") != "jaff.network_json":
        raise ValueError("Not a jaff.network_json file")
    if payload.get("schema_version") != 1:
        raise ValueError(
            f"Unsupported Network schema_version={payload.get('schema_version')!r}"
        )

    net_data: JaffProps = {
        "file_name": Path(payload.get("file_name")),
        "label": payload.get("label"),
        "species": [],
        "species_dict": {},
        "reactions": [],
    }

    species_payload = payload.get("species") or []
    if not isinstance(species_payload, list):
        raise ValueError("Invalid species list in JSON")

    # Create species list in index order.
    by_index = {}
    for spj in species_payload:
        if not isinstance(spj, dict):
            raise ValueError("Invalid species entry in JSON")
        name = spj.get("name")
        idx = spj.get("index")
        if not isinstance(name, str) or not isinstance(idx, int):
            raise ValueError("Invalid species name/index in JSON")
        if idx in by_index:
            raise ValueError(f"Duplicate species index {idx}")
        by_index[idx] = name

    species_by_index = {}
    species_list = []
    species_dict = {}
    mass_dict = load_mass_dict()

    for idx in sorted(by_index.keys()):
        name = by_index[idx]
        sp_obj = Species(name, mass_dict, idx)
        species_list.append(sp_obj)
        species_dict[name] = idx
        species_by_index[idx] = sp_obj

    net_data["species"] = species_list
    net_data["species_dict"] = species_dict

    rate_symbols_payload = payload.get("rate_symbols") or []
    rate_symbol_assumptions = {}
    if isinstance(rate_symbols_payload, list):
        for item in rate_symbols_payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            assumptions = item.get("assumptions") or {}
            if not isinstance(name, str) or not isinstance(assumptions, dict):
                continue
            rate_symbol_assumptions[name] = {
                k: v
                for k, v in assumptions.items()
                if isinstance(k, str) and isinstance(v, bool)
            }

    def apply_symbol_assumptions(expr):
        if not rate_symbol_assumptions:
            return expr
        symbols = [s for s in expr.free_symbols if s.name in rate_symbol_assumptions]
        if not symbols:
            return expr
        replacements = {}
        for sym in symbols:
            assumptions = rate_symbol_assumptions.get(sym.name, {})
            replacements[sym] = Symbol(sym.name, **assumptions)
        return expr.xreplace(replacements)

    def decode_maybe_sympy(node):
        if node is None:
            return None
        if isinstance(node, dict):
            kind = node.get("kind")
            if kind == "string":
                value = node.get("value")
                if not isinstance(value, str):
                    raise ValueError("Invalid string value encoding")
                return value
            if kind is not None:
                raise ValueError(f"Unknown encoded value kind={kind!r}")
        if isinstance(node, (dict, list, int, float)):
            return apply_symbol_assumptions(sympy_from_jsonable(node))
        raise ValueError("Invalid encoded value")

    reactions_payload = payload.get("reactions") or []
    if not isinstance(reactions_payload, list):
        raise ValueError("Invalid reactions list in JSON")

    for rj in reactions_payload:
        if not isinstance(rj, dict):
            raise ValueError("Invalid reaction entry in JSON")
        reactants_idx = rj.get("reactants") or []
        products_idx = rj.get("products") or []
        if not isinstance(reactants_idx, list) or not isinstance(products_idx, list):
            raise ValueError("Invalid reactants/products list in JSON")
        try:
            reactants = [species_by_index[int(i)] for i in reactants_idx]
            products = [species_by_index[int(i)] for i in products_idx]
        except Exception as e:
            raise ValueError(f"Invalid species indices in reaction: {e}") from e

        rate = decode_maybe_sympy(rj.get("rate"))
        dE = decode_maybe_sympy(rj.get("dE"))
        dRad_dt = rj.get("dRad_dt")
        custom_rad_rate = rj.get("custom_rad_rate")
        tmin = rj.get("tmin")
        tmax = rj.get("tmax")
        original_string = rj.get("original_string") or ""
        xsecs = rj.get("xsecs")

        net_data["reactions"].append(
            {
                "reactants": reactants,
                "products": products,
                "rate": rate,
                "dE": dE,
                "dRad_dt": dRad_dt,
                "custom_rad_rate": custom_rad_rate,
                "tmin": tmin,
                "tmax": tmax,
                "original_string": original_string,
                "xsecs_dict": xsecs,
            }
        )

    return net_data
