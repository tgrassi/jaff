from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

import numpy as np
from sympy import Basic, Symbol, __version__, expand_log, lambdify, log, srepr, symbols
from sympy.core.function import AppliedUndef

from .. import __version__ as jaff_version
from ..common import SCHEMA_VERSION as SYMPY_SCHEMA
from ..common import fast_log2, inverse_fast_log2, is_jaff_file, load_mass_dict
from ..common import from_jsonable as sympy_from_jsonable
from ..common import to_jsonable as sympy_to_jsonable
from ..core.logger import JaffLogger
from ..drivers.hdf5 import HDF5
from ..errors import NotJaffFileError
from ..jaff_types import HDF5Dict

if TYPE_CHECKING:
    from .. import Network, Reaction, Specie, Species
else:
    Specie = "Specie"
    Species = "Species"
    Reaction = "Reaction"
    Network = "Network"

ReactionProps = TypedDict(
    "ReactionProps",
    {
        "reactants": list["Specie"],
        "products": list["Specie"],
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
        "species": Species,
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
        "file_name": str(net.file_name),
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
    from .. import Specie, Species

    if isinstance(filename, str):
        filename = Path(filename)

    if not filename.exists():
        raise FileNotFoundError(filename)

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
        "species": Species(),
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
    species_list = Species()
    mass_dict = load_mass_dict()

    for idx in sorted(by_index.keys()):
        name = by_index[idx]
        sp_obj = Specie(name, mass_dict, idx)
        species_list.add(sp_obj)
        species_by_index[idx] = sp_obj

    net_data["species"] = species_list

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


def get_table(
    reactions: list[Reaction],
    logger: logging.Logger | None,
    T_min=None,
    T_max=None,
    nT=64,
    err_tol=0.01,
    rate_min=1e-30,
    rate_max=1e100,
    fast_log=False,
    verbose=False,
):
    """
    Return a tabulation of rate coefficients as a function of
    temperature for all reactions.

    Parameters
    ----------
        T_min : float or None
            minimum temperature for the tabulation; if left as None,
            will be set to the minimum temperature over reactions in
            the network
        T_max : float or None
            maximum temperature for the tabulation; if left as None,
            will be set to the maximum temperature over reactions in
            the network
        nT : int
            initial guess for number of sampling temperatures
        err_tol : float or None
            relative error tolerance for interpolation; if set to
            None, adaptive resampling is disabled and the table size
            will be exactly nT
        rate_min : float
            adaptive error tolerance is not applied to rates below
            rate_min
        rate_max : float
            rataes above rate_max are clipped to rate_max to prevent
            overflow
        fast_log : bool
            if True, sample points are equally spaced in fast_log2(T)
            rather than log(T)
        verbose : bool
            if True, produce verbose output while adaptively refining

    Returns
    -------
        temp : array, shape (nTemp)
            gas temperatures at which rates are sampled
        coeff : array, shape (nreact, nTemp)
            tabulated reaction rate coefficients at temperatures temp

    Notes
    -----
        1) By default temperature is sampled logarithmically in the
        output, i.e., temp =
        np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
        where nTemp is the number of temperatures in the output
        table. If fast_log is set to True, then the outputs are
        instead uniformly spaced in fast_log2 rather than the
        true logarithm.
        2) For reaction rates that depend on something other than
        tgas, the results are computed at av = 0 and crate = 1;
        rates that depend on any other quantities are not tabulated,
        and the table entries for such reactions will be set to NaN.
        3) Adaptive sampling is performed by comparing the results
        of a logarithmic interpolation between each rate
        coefficient at each pair of sampled temperature with
        a calculation of the exact rate coefficient at a temperature
        halfway between the two sample points; the errors is taken
        to be abs((interp_value - exact_value) / (exact_value + rate_min)),
        and nTemp is increased until the error for all coefficients
        is below tolerance.
    """

    if logger is None:
        logger = JaffLogger().get_logger()

    # Get min and max temperature if not provided
    if T_min is None:
        T_min = np.nanmin([r.tmin if r.tmin is not None else np.nan for r in reactions])
    if T_max is None:
        T_max = np.nanmax([r.tmax if r.tmax is not None else np.nan for r in reactions])
    if T_min is None or T_max is None:
        raise ValueError(
            "could not determine T_min or T_max from "
            "reaction list; set T_min and T_max manually"
        )

    # First step: for each reaction, create a sympy object we can
    # use to substitute to get an expression in terms of the
    # primitive variables
    react_sympy = [r.get_sympy() for r in reactions]

    # Second step: set av = 0 and crate = 1
    react_subst = []
    for r in react_sympy:
        r = r.subs(symbols("av"), 0.0)
        r = r.subs(symbols("crate"), 1.0)
        react_subst.append(r)

    # Third step: create numpy fucntions for each reaction
    react_func = []
    for i, r in enumerate(react_subst):
        if len(r.free_symbols) == 0:
            # Reaction rates that are just constants; in this
            # case just copy that constant to the list of functions
            react_func.append(np.log(float(r)))
        elif (
            (len(r.free_symbols) > 1)
            or (symbols("tgas") not in r.free_symbols)
            or ("Function" in srepr(r))
        ):
            # For reaction rates that do not depend on temperature,
            # that depend on variables other than temperature,
            # or that contain arbitrary functions, we cannot
            # tabulate, so just store None
            react_func.append(None)
        else:
            # Case of reactions that depend only on temperature; to
            # avoid overflows we will take the log of the rate function
            # and expand it before converting to numpy, and then we will
            # exponentiate at the very end
            logr = expand_log(log(r))
            react_func.append(lambdify(symbols("tgas"), logr, "numpy"))

    # Fourth step: generate rate coefficient table for initial guess
    # table size
    nTemp = nT
    if not fast_log:
        temp = np.logspace(np.log10(T_min), np.log10(T_max), nTemp)
    else:
        # Generate sample points that are uniformly sampled in fast_log2
        log_temp_min = fast_log2(T_min)
        log_temp_max = fast_log2(T_max)
        log_temp = np.linspace(log_temp_min, log_temp_max, nTemp)
        temp = inverse_fast_log2(log_temp)
    log_rates = np.zeros((len(react_func), nTemp))
    for i, f in enumerate(react_func):
        if isinstance(f, float):
            log_rates[i, :] = f
        elif f is None:
            log_rates[i, :] = np.nan
        else:
            # Note: it would be much faster to do this via an array operation
            # rather than a list comprehension, but sympy (as of v1.13) does
            # not consistently generate numpy expressions that work properly
            # with vector inputs, so restricting the input to scalars is safer.
            f_eval = np.array([f(t) for t in temp])
            log_rates[i, :] = np.clip(f_eval, a_min=None, a_max=np.log(rate_max))

    # Fifth step: do adaptive growth of table
    if err_tol is not None:
        while True:
            # Compute estimates at half-way points
            nTemp = 2 * nTemp - 1
            temp_grow = np.zeros(nTemp)
            temp_grow[::2] = temp
            if not fast_log:
                temp_grow[1::2] = np.sqrt(temp[1:] * temp[:-1])
            else:
                log_temp_lo = fast_log2(temp[:-1])
                log_temp_hi = fast_log2(temp[1:])
                temp_grow[1::2] = inverse_fast_log2(0.5 * (log_temp_lo + log_temp_hi))
            log_rates_grow = np.zeros((len(react_func), nTemp))
            log_rates_grow[:, ::2] = log_rates
            log_rates_approx = np.zeros((len(react_func), (nTemp - 1) // 2))
            for i, f in enumerate(react_func):
                if isinstance(f, float):
                    log_rates_grow[i, 1::2] = f
                    log_rates_approx[i, :] = f
                elif f is None:
                    log_rates_grow[i, 1::2] = np.nan
                    log_rates_approx[i, :] = np.nan
                else:
                    # See comment above about why we're using a list comprehension
                    # here instead of a straight array operation
                    f_eval = np.array([f(t) for t in temp_grow[1::2]])
                    log_rates_grow[i, 1::2] = np.clip(
                        f_eval, a_min=None, a_max=np.log(rate_max)
                    )
                    log_rates_approx[i, :] = 0.5 * (
                        log_rates_grow[i, :-1:2] + log_rates_grow[i, 2::2]
                    )

            # Copy new estimates to current ones
            temp = temp_grow
            log_rates = log_rates_grow

            # Make error estimate
            rel_err = np.abs(
                (np.exp(log_rates_approx) - np.exp(log_rates[:, 1::2]))
                / (np.exp(log_rates[:, 1::2]) + rate_min)
            )
            max_err = np.nanmax(rel_err)

            # Print output if verbose
            if verbose:
                idx_max = np.unravel_index(np.nanargmax(rel_err), rel_err.shape)
                logger.info(
                    f"nTemp = {nTemp}, max_err = {max_err} in reaction "
                    f"{reactions[idx_max[0]].get_verbatim()} at T = {temp[idx_max[1]]}"
                )

            # Check for convergence
            if max_err < err_tol:
                break

    # Return final table
    return temp, np.exp(log_rates)


def write_data_table(
    reactions: list[Reaction],
    logger: logging.Logger | None,
    fname: str | Path,
    label: str | None = None,
    T_min=None,
    T_max=None,
    nT=64,
    err_tol=0.01,
    rate_min=1e-30,
    rate_max=1e100,
    fast_log=False,
    format="auto",
    include_all=False,
    verbose=False,
):
    """
    Write a tabulation of rate coefficients as a function of
    temperature for all reactions.

    Parameters
    ----------
        fname : string
            name of output file
        T_min : float or None
            minimum temperature for the tabulation; if left as None,
            will be set to the minimum temperature over reactions in
            the network
        T_max : float or None
            maximum temperature for the tabulation; if left as None,
            will be set to the maximum temperature over reactions in
            the network
        nT : int
            initial guess for number of sampling temperatures
        err_tol : float or None
            relative error tolerance for interpolation; if set to
            None, adaptive resampling is disabled and the table size
            will be exactly nT
        rate_min : float
            adaptive error tolerance is not applied to rates below
            rate_min
        rate_max : float
            rates above rate_max are clipped to rate_max to prevent
            overflow
        fast_log : bool
            if True, sample points are equally spaced in fast_log2(T)
            rather than log(T)
        format : 'auto' | 'txt' | 'hdf5'
            output format; if set to 'auto', format will be guessed from
            extension of fname, otherwise output will be set to either
            text for hdf5 format
        include_all : bool
            if True, the output table will contain all reactions, with
            entries for rate coefficients that cannot be tabulated
            just as a function of temperature set to NaN; if False,
            the output table only includes coefficients that can be
            tabulated and are non-constant
        verbose : bool
            if True, produce verbose output while adaptively refining

    Returns
    -------
        Nothing

    Raises
    ------
        ValueError
            if format is set to 'auto' and the extension is of fname
            is not 'txt', 'hdf', or 'hdf5'
        IOError
            if the output fille cannot be opened

    Notes
    -----
        See notes to get_table for details on how temperature sampling
        and error tolerance is handled.
    """
    if logger is None:
        logger = JaffLogger().get_logger()

    if isinstance(fname, str):
        fname = Path(fname)

    supported_formats = ["auto", "hdf5", "txt"]
    supported_extensions = [".hdf", ".hdf5", ".txt"]

    if format not in supported_formats:
        raise ValueError(
            f"Unknown output format {format}\n"
            f"Supported output formats are {', '.join(supported_formats)}"
        )

    # Deduce output format
    if format in supported_formats and format != "auto":
        out_type = supported_formats[supported_formats.index(format)]
    elif format == "auto":
        if fname.suffix in supported_extensions:
            out_type = supported_extensions[supported_extensions.index(fname.suffix)]
        else:
            raise ValueError(
                f"Cannot deduce output type from extension for file: {fname}\n"
                f"Supported extensions are .txt, .hdf5 and .hdf"
            )

    if label is None:
        label = fname.stem

    # Get rate coefficients
    temp, coef = get_table(
        reactions=reactions,
        logger=logger,
        T_min=T_min,
        T_max=T_max,
        nT=nT,
        err_tol=err_tol,
        rate_min=rate_min,
        rate_max=rate_max,
        fast_log=fast_log,
        verbose=verbose,
    )

    # Remove from table reaction rates that are either constant
    # or NaN
    if include_all:
        react_list = list(range(len(coef)))
    else:
        react_list = []
        for i, c in enumerate(coef):
            if np.sum(np.isnan(c)) > 0 or np.amax(c) - np.amin(c) == 0.0:
                continue
            react_list.append(i)
    coef = coef[react_list]

    # For the reactions that we are including, grab the reaction
    # type and lists of reactants and products
    rtype = []
    reactants = []
    products = []
    for i in react_list:
        if reactions[i].guess_type() == "unknown":
            rtype.append("2_body")
        else:
            rtype.append(reactions[i].guess_type())
        reactants_ = {}
        for r in reactions[i].reactants:
            if r.name in reactants_.keys():
                reactants_[r.name] += 1
            else:
                reactants_[r.name] = 1
        reactants.append(reactants_)
        products_ = {}
        for p in reactions[i].products:
            if p.name in products_.keys():
                products_[p.name] += 1
            else:
                products_[p.name] = 1
        products.append(products_)

    def to_text():
        # Text output
        with open(fname) as fp:
            # Write header
            fp.write("# JAFF auto-generated rate coefficient table\n")
            fp.write(f"# Network name: {label}\n")
            fp.write("# Reactions included\n")
            fp.write("#   (reactants) (products) (reaction type)\n")
            for rt, r, p in zip(rtype, reactants, products):
                fp.write(f"#   {r} {p} {rt}\n")

            # Write data in quokka table format
            fp.write("1\n")  # Table is 1d
            fp.write(f"{len(coef)}\n")  # N outputs per table entry
            if fast_log:
                fp.write("3\n")  # Table is uniform in fast_log
            else:
                fp.write("2\n")  # Table is uniform in log
            fp.write(f"{len(temp)}\n")  # Number of temperature entries
            fp.write(f"{temp[0]} {temp[-1]}\n")  # Min/max temperature

            # Now write the data
            for c in coef:
                for c_ in c:
                    fp.write(f"{c_} ")
                fp.write("\n")

    def to_hdf5():
        output_names = []
        output_units = []
        for i, rt, r, p in zip(range(len(rtype)), rtype, reactants, products):
            output_names.append(f"{rt} rate coefficient: {r} --> {p}")
            output_units.append("cm^3 s^-1")

        hdfdict = HDF5Dict(
            {
                "reaction_coeff": {
                    "_attrs": {
                        "input_names": ["temperature"],
                        "input_units": ["K"],
                        "xlo": np.array([temp[0]]),
                        "xhi": np.array([temp[-1]]),
                        "spacing": ["fast_log"] if fast_log else ["log"],
                    },
                    "output_names": {
                        "_data": output_names,
                        "_dtype": "s",
                        "_kind": "linear",
                    },
                    "output_units": {
                        "_data": output_units,
                        "_dtype": "s",
                        "_kind": "linear",
                    },
                    "data": {
                        "_data": coef,
                        "_kind": "linear",
                    },
                }
            }
        )

        HDF5().from_dict(fname, hdfdict)

    # Write output in appropriate format
    if out_type == "txt":
        to_text()
    elif out_type == "hdf5":
        to_hdf5()
