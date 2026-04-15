import gzip
import json
import logging
import os
import re
import sys
from pathlib import Path
from textwrap import dedent
from typing import NotRequired, TypedDict

import h5py
import numpy as np
import sympy
from sympy import (
    Basic,
    Expr,
    Float,
    Function,
    Idx,
    MatrixSymbol,
    Max,
    Min,
    Piecewise,
    Symbol,
    lambdify,
    parse_expr,
    srepr,
    symbols,
)
from sympy.core.function import AppliedUndef, UndefinedFunction
from tqdm import tqdm

from .auxilary_file_parser import AuxilaryFunctionParser, FunctionsDict
from .common import resolve_symbolic_dependencies
from .common.helper import resolve_dependencies
from .core.logger import JaffLogger
from .drivers.sqlite import JaffDb
from .errors.parser import ParserError
from .fastlog import fast_log2, inverse_fast_log2
from .network_parser import NetworkParser
from .photochemistry import Photochemistry
from .radiation import Radiation
from .reaction import Reaction
from .species import Species

NetworkProps = TypedDict(
    "NetworkProps",
    {
        "fname": str,
        "errors": NotRequired[bool],
        "label": NotRequired[str],
        "funcfile": NotRequired[str],
        "replace_nH": NotRequired[bool],
        "rad_bands": NotRequired[list],
        "rad_powerlaw_index": NotRequired[int | float],
        "rad_energy_density": NotRequired[bool],
        "c": NotRequired[float],
    },
)

ElementProps = TypedDict(
    "ElementProps",
    {
        "name": str,
        "mass": float,
    },
)


class Network:
    # ****************
    def __init__(
        self,
        fname,
        errors=False,
        label=None,
        funcfile=None,
        replace_nH=True,
        rad_bands=[],
        rad_powerlaw_index: int | float = 0,
        rad_energy_density: bool = False,
        c: float = 2.99792458e10,  # Speed of light in cgs unit
    ):
        self.logger: logging.Logger = JaffLogger().get_logger()
        self.motd()

        # Get the path to the data file relative to this module
        self.mass_dict: dict[str, ElementProps] = {}
        self.species = []
        self.species_dict = {}
        self.reactions_dict = {}
        self.reactions: list[Reaction] = []
        self.rlist = self.plist = None
        self.dEdt_chem = Float(0.0)
        self.dEdt_other = Float(0.0)
        self.file_name = fname
        self.label = label if label else os.path.basename(fname).split(".")[0]
        self.radiation: Radiation | None = (
            Radiation(rad_bands, rad_powerlaw_index, rad_energy_density, c)
            if rad_bands
            else None
        )
        self.dRad_dt_extra = Float(0.0)

        self.logger.info(f"Loading network from {fname}")
        self.logger.info(f"Network label: {self.label}")

        self.load_mass_dict()
        self.photochemistry = Photochemistry()

        self.load_network(fname, funcfile, replace_nH)
        self.__calculate_nework_extras(replace_nH)

        self.check_sink_sources(errors)
        self.check_recombinations(errors)
        self.check_isomers(errors)
        self.check_unique_reactions(errors)

        self.generate_reactions_dict()
        self.generate_reaction_matrices()

        print("\nAll done!\n")

    # ****************
    @staticmethod
    def motd():
        try:
            with open("assets/words.dat", "r") as f:
                words = f.readlines()
            words = [
                x.strip()
                for x in words
                if x.lower().startswith("f") and x.strip().isalpha()
            ]
            fword = np.random.choice(words)
        except (FileNotFoundError, PermissionError, OSError, ValueError):
            fword = "Fancy"
        welcome_text = dedent("""
        Welcome to\n
        ░░█ ▄▀█ █▀▀ █▀▀
        █▄█ █▀█ █▀░ █▀░
        """)
        print(welcome_text)
        print(f"Just Another {fword.title()} Format!\n")

    def load_mass_dict(self) -> None:
        with JaffDb() as jdb:
            rows = jdb.table("atomic_masses").all_rows()

        self.mass_dict = {}
        for row in rows:
            self.mass_dict[row["element"]] = {"mass": row["mass"], "name": row["name"]}

    def load_network(
        self,
        fname,
        funcfile,
        replace_nH,
    ):
        specie_names = set()
        # All variables found in the rate expressions (not in the custom variables)
        free_symbols = set()
        undef_funcs = set()
        interp_funcs = set()

        # number of photo-reactions
        n_photo = 0
        tgas = symbols("tgas")

        with NetworkParser(fname, self.logger) as netp:
            reactions_list, global_vars = netp.get_parsed()

        # Read the auxiliary function file to get the list of functions
        # to substitute
        aux_funcs = self.read_aux_funcs(funcfile)

        global_vars = {
            var: resolve_dependencies(expr, {}, aux_funcs)
            for var, expr in global_vars.items()
        }
        subs_dict: dict[Basic, Basic] = {
            symbols(var.lower()): expr for var, expr in global_vars.items()
        }

        for i, reaction in enumerate(
            tqdm(reactions_list, desc=f"Creating {self.label} network", unit=" reactions")
        ):
            reactants: list[str] = reaction["r"]
            products: list[str] = reaction["p"]
            tmin: float | None = reaction["tmin"]
            tmax: float | None = reaction["tmax"]
            rate: str = reaction["rate"]
            aux_chem_rate = f"chemrate{i}"
            aux_delta_rad = f"deltarad{i}"
            aux_delta_e = f"deltae{i}"

            # Handle reactants and products
            for s in reactants + products:
                if s not in specie_names:
                    specie_names.add(s)
                    self.species.append(Species(s, self.mass_dict, len(specie_names) - 1))
                    self.species_dict[s] = self.species[-1].index

            rr = [self.species[self.species_dict[r]] for r in reactants]
            pp = [self.species[self.species_dict[p]] for p in products]

            local_subs_dict = {**subs_dict}

            # Handle rate
            local_subs_dict[tgas] = (
                Max(Min(tgas, tmax), tmin)
                if tmin and tmax
                else Max(tgas, tmin)
                if tmin
                else Min(tgas, tmax)
                if tmax
                else tgas
            )
            for sym, expr in local_subs_dict.items():
                if sym != tgas and expr.has(tgas):
                    local_subs_dict[sym] = expr.xreplace({tgas: local_subs_dict[tgas]})

            rate_expr, is_photoreaction, n_photo = self.__parse_rate(
                aux_chem_rate, rate, aux_funcs, global_vars, n_photo
            )
            rate_expr = resolve_dependencies(rate_expr, local_subs_dict, aux_funcs)

            # Resolve other functions

            # Read auxilary photon addition/consumption rate
            # which will be weighted and added to the moment 0
            # equation in each band
            deltaRad: Basic = Float(0.0)
            if aux_delta_rad in aux_funcs:
                deltaRad = aux_funcs[aux_delta_rad]["def"]

            # If there is a deltaE function describing change in
            # chemical energy associated with this reaction, add
            # an appropriate term to the dEdt_chem for this network.
            deltaE: Basic = Float(0.0)
            if aux_delta_e in aux_funcs:
                deltaE = aux_funcs[aux_delta_e]["def"]

            for expr in [rate_expr, deltaE, deltaRad]:
                free_symbols |= self.free_symbols(expr)
                self.__detect_undefined_functions(expr, undef_funcs, interp_funcs)

            # Handle reaction
            rea = Reaction(
                rr, pp, rate_expr, tmin, tmax, deltaE, deltaRad, reaction["string"]
            )
            # Save to reaction list
            self.reactions.append(rea)

            if is_photoreaction and self.radiation is not None:
                if aux_chem_rate not in aux_funcs:
                    self.radiation.set_reaction_rate_coefficient(rea)
                elif aux_chem_rate in aux_funcs and aux_delta_rad:
                    self.radiation.set_custom_rate(rea)
                else:
                    raise ParserError(
                        "If radiation is enabled and a custom rate is supplied\n"
                        "for a photo reaction, the auxilary deltaRad function is\n"
                        "necessary to weigh the first moment radiation equations\n"
                        f"Please add a custom deltaRad function for reaction {i}"
                    )

            if rea.guess_type() == "photo":
                rea.xsecs_dict = self.photochemistry.get_xsec(rea)

        # Add chemical and non-chemical heating and cooling rates
        if "heatingcoolingrate" in aux_funcs:
            self.dEdt_other = aux_funcs["heatingcoolingrate"]["def"]
            self.dEdt_other = self.standardize_symbols(self.dEdt_other, replace_nH)
            free_symbols |= self.free_symbols(self.dEdt_other)
            self.__detect_undefined_functions(self.dEdt_other, undef_funcs, interp_funcs)

        self.logger.info(
            f"Variables found: {', '.join(sorted(str(s) for s in free_symbols))}"
        )
        self.logger.info(f"Loaded {len(self.reactions)} reactions")
        self.logger.info(f"Loaded {n_photo} photo-chemistry reactions")

        # Issue warning message if undefined functions remain
        if interp_funcs:
            self.logger.info(
                f"Found the following interpolation functions: {', '.join(interp_funcs)}"
            )
        if undef_funcs:
            self.logger.warning(f"Found undefined functions {', '.join(undef_funcs)}")

    def __calculate_nework_extras(self, replace_nH):
        # Apply replacement rules to replace standard symbols
        # appearing in rates with terms involving known species
        nden = MatrixSymbol("nden", len(self.species), 1)
        for r in self.reactions:
            r.rate = self.standardize_symbols(r.rate, replace_nH)
            dE_dt = r.dE * r.rate
            for s in r.reactants:
                dE_dt *= nden[self.species_dict[s.name]]
            self.dEdt_chem += dE_dt
            self.dRad_dt_extra += r.dRad_dt
        self.dEdt_chem = self.standardize_symbols(self.dEdt_chem, replace_nH)
        self.dRad_dt_extra = self.standardize_symbols(self.dRad_dt_extra, replace_nH)

    @staticmethod
    def __parse_rate(
        aux_chem_rate: str,
        rate: str,
        aux_funcs: dict[str, FunctionsDict],
        global_vars: dict[str, Basic],
        n_photo: int,
    ) -> tuple[Basic, bool, int]:
        is_photoreaction = False
        if aux_chem_rate in aux_funcs:
            rate_expr = aux_funcs[aux_chem_rate]["def"]
        elif rate in global_vars:
            rate_expr = symbols(rate)
        elif "photo" in rate.lower():
            is_photoreaction = True
            f: UndefinedFunction = Function("photorates")  # type: ignore
            n_photo += 1

            match = re.match(r"(?i:photo)\((.*?)\)", rate)
            if match:
                args_str = match.group(1)
                photo_args: list[str | float] = [
                    arg.strip() for arg in args_str.split(",") if arg.strip()
                ]
                while len(photo_args) < 2:
                    photo_args.append(1.0e99)

                rate_expr = f(n_photo, photo_args[0], photo_args[1])
            else:
                photo_args: list[str | float] = [
                    arg.strip() for arg in rate.split(",") if arg.strip()
                ]
                while len(photo_args) < 3:
                    photo_args.append(1.0e99)

                rate_expr = f(n_photo, photo_args[1], photo_args[2])
        else:
            rate_expr = parse_expr(rate, evaluate=False)

        return rate_expr, is_photoreaction, n_photo

    @staticmethod
    def __detect_undefined_functions(
        expr: sympy.Expr, undef_funcs: set, interp_funcs: set
    ) -> None:
        for f in expr.atoms(AppliedUndef):
            if "interp" in f.func.__name__:
                interp_funcs |= {f.func.__name__}
                continue
            undef_funcs |= {f.func.__name__}

    # ****************
    def read_aux_funcs(self, funcfile: str | Path | None) -> dict:
        """
        Read the auxiliary function file

        Parameters:
            funcfile : string or None
                Name of auxiliary function file; if left as None,
                the default name self.file_name+"_functions' is used,
                and if set to the string 'none' then no auxiliary
                functions will be read

        Returns:
            funcs : dict
                a dict whose keys are the names of functions and
                whose values are dicts containing the fields "def",
                "args", and "argcomments"; "def" contains a Sympy
                expression giving the function definition, "args"
                contains a list of Sympy.Symbols defining the
                arguments, "comments" is a string that captures any
                comments the follow the function definition,
                and "argcomments" is a list of strings capturing
                comments on the definitions of the arguments.

        Raises:
            IOError, if the file does not exist or cannot be parsed
        """
        if funcfile == "none":
            return {}

        if funcfile is None:
            funcfiles_list = [
                Path(f"{self.file_name}.jfunc"),
                Path(self.file_name).with_suffix(".jfunc"),
            ]

            funcfile_exists: bool = False
            for f in funcfiles_list:
                if f.exists():
                    funcfile = f
                    funcfile_exists = True
                    break

            if not funcfile_exists:
                return {}

        assert funcfile is not None

        if isinstance(funcfile, str):
            funcfile = Path(funcfile)

        if not funcfile.exists():
            raise FileNotFoundError(f"Auxilary functions file not found: {funcfile}")

        with AuxilaryFunctionParser(funcfile) as afp:
            func_dict: FunctionsDict = afp.get_dict()

        return func_dict

    # ****************
    def to_jaff_file(self, filename):
        """
        Serialize this Network to a .jaff file (gzip-compressed JSON payload).

        Notes:
            - Uses a versioned, whitelisted SymPy JSON AST for expressions.
            - Excludes photochemistry-specific runtime state; reactions may still
              include xsecs if present.
            - Files are written with gzip compression even when the filename ends
              with `.jaff` (no `.gz` suffix).
        """
        filename = os.fspath(filename)
        if not (str(filename).endswith(".jaff") or str(filename).endswith(".jaff.gz")):
            raise ValueError(
                "Network.to_jaff_file requires a filename ending with '.jaff' or '.jaff.gz'"
            )

        from . import __version__ as jaff_version
        from .sympy_json import SCHEMA_VERSION as SYMPY_SCHEMA
        from .sympy_json import to_jsonable as sympy_to_jsonable

        def has_undefined_functions(expr):
            if not isinstance(expr, sympy.Basic):
                return False
            for f in expr.atoms(Function):
                if type(f.func) is UndefinedFunction:
                    return True
            return False

        def encode_maybe_sympy(value):
            if isinstance(value, str):
                return {"kind": "string", "value": value}
            if isinstance(value, sympy.Basic):
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
            "sympy_version": sympy.__version__,
            "label": self.label,
            "file_name": self.file_name,
            "species": [
                {
                    "name": sp.name,
                    "index": int(sp.index),
                    "mass": float(sp.mass) if sp.mass is not None else None,
                    "charge": int(sp.charge) if sp.charge is not None else None,
                }
                for sp in self.species
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
                        for r in self.reactions
                        if isinstance(r.rate, sympy.Basic)
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
                    "original_string": r.original_string,
                    "xsecs": jsonable(r.xsecs_dict),
                }
                for r in self.reactions
            ],
        }

        with gzip.open(filename, "wt", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)

    # ****************
    @classmethod
    def from_jaff_file(cls, filename, *, errors=False):
        """
        Deserialize a Network previously written by Network.to_jaff_file.

        Parameters:
            filename : str
                `.jaff` file to read (gzip-compressed JSON by default; legacy
                uncompressed JSON is also supported).
            errors : bool
                If True, run Network validation checks and exit on errors.
        """
        from .sympy_json import from_jsonable as sympy_from_jsonable

        filename = os.fspath(filename)

        # Prefer gzip if the filename indicates it; otherwise, sniff the magic header
        # so we can transparently read both compressed and legacy uncompressed files.
        use_gzip = str(filename).endswith(".gz")
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

        # Build an instance without going through __init__ (which parses files).
        net = cls.__new__(cls)

        # Minimal initialization of attributes expected by other methods.
        net.file_name = payload.get("file_name")
        net.label = payload.get("label")
        net.reactions = []
        net.reactions_dict = {}
        net.species = []
        net.species_dict = {}
        net.rlist = net.plist = None
        net.photochemistry = Photochemistry()

        # Load default mass dict (same source as __init__).
        net.load_mass_dict()

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
        for idx in sorted(by_index.keys()):
            name = by_index[idx]
            sp_obj = Species(name, net.mass_dict, idx)
            net.species.append(sp_obj)
            net.species_dict[name] = idx
            species_by_index[idx] = sp_obj

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
                replacements[sym] = sympy.Symbol(sym.name, **assumptions)
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
            tmin = rj.get("tmin")
            tmax = rj.get("tmax")
            original_string = rj.get("original_string") or ""
            xsecs = rj.get("xsecs")

            rea = Reaction(
                reactants=reactants,
                products=products,
                rate=rate,
                tmin=tmin,
                tmax=tmax,
                dRad_dt=parse_expr("0.0"),  # Support for drad_dt will be added soon
                dE=dE or parse_expr("0"),
                original_string=original_string,
                errors=False,
            )
            rea.xsecs_dict = xsecs
            net.reactions.append(rea)

        # Recompute derived structures.
        net.generate_reactions_dict()
        net.generate_reaction_matrices()

        # Recompute dEdt_chem, matching load_network behavior.
        net.dEdt_chem = parse_expr("0")
        nden = MatrixSymbol("nden", len(net.species), 1)
        for r in net.reactions:
            dE_dt = r.dE * r.rate
            for s in r.reactants:
                dE_dt *= nden[Idx(net.species_dict[s.name])]
            net.dEdt_chem += dE_dt

        if errors:
            net.check_sink_sources(errors=True)
            net.check_recombinations(errors=True)
            net.check_isomers(errors=True)
            net.check_unique_reactions(errors=True)

        return net

    @staticmethod
    def free_symbols(expr: Basic) -> set[Basic]:
        return {fs for fs in expr.free_symbols if "nden" not in str(fs)}

    # ****************
    def compare_reactions(self, other, verbosity=1):
        print(f'Comparing networks "{self.label}" and "{other.label}"...')

        net1 = [x.serialized for x in self.reactions]
        net2 = [x.serialized for x in other.reactions]

        nsame = 0
        nmissing1 = 0
        nmissing2 = 0
        for ref in np.unique(net1 + net2):
            if ref in net1 and ref not in net2:
                rea = self.get_reaction_by_serialized(ref)
                nmissing2 += 1
                if verbosity > 0:
                    print(
                        f'Found in "{self.label}" but not in "{other.label}": {rea.get_verbatim()}'
                    )

            elif ref in net2 and ref not in net1:
                rea = other.get_reaction_by_serialized(ref)
                nmissing1 += 1
                if verbosity > 0:
                    print(
                        f'Found in "{other.label}" but not in "{self.label}": {rea.get_verbatim()}'
                    )
            else:
                if verbosity > 1:
                    print(f"Found in both networks: {ref}")
                nsame += 1

        print(f"Found {nsame} reactions in common")
        print(f'{nmissing1} reactions missing in "{self.label}"')
        print(f'{nmissing2} reactions missing in "{other.label}"')

    # ****************
    def compare_species(self, other, verbosity=1):
        print(f'Comparing species in networks "{self.label}" and "{other.label}"...')

        net1 = [x.serialized for x in self.species]
        net2 = [x.serialized for x in other.species]

        same_species = []
        only_in_self = []
        only_in_other = []
        nmissing1 = 0
        nmissing2 = 0
        for ref in np.unique(np.array(net1 + net2)):
            if ref in net1 and ref not in net2:
                sp = self.get_species_by_serialized(ref)
                nmissing2 += 1
                if verbosity > 1:
                    print(
                        f'Found in "{self.label}" but not in "{other.label}": {sp.name}'
                    )
                only_in_self.append(sp)

            elif ref in net2 and ref not in net1:
                sp = other.get_species_object(ref)
                nmissing1 += 1
                if verbosity > 1:
                    print(
                        f'Found in "{other.label}" but not in "{self.label}": {sp.name}'
                    )
                only_in_other.append(sp)
            else:
                sp = self.get_species_by_serialized(ref)
                if verbosity > 1:
                    print(f"Found in both networks: {ref}")
                same_species.append(sp)

        print(
            f"Found {len(same_species)} species in common: {sorted([x.name for x in same_species])}"
        )
        print(
            f'Found {len(only_in_self)} species in "{self.label}" but not in "{other.label}": {sorted([x.name for x in only_in_self])}'
        )
        print(
            f'Found {len(only_in_other)} species in "{other.label}" but not in "{self.label}": {sorted([x.name for x in only_in_other])}'
        )

    # ****************
    def check_sink_sources(self, errors):
        pps = []
        rrs = []
        for rea in self.reactions:
            for p in rea.products:
                pps.append(p.name)
            for r in rea.reactants:
                rrs.append(r.name)

        has_sink = has_source = False
        for s in self.species:
            if s.name == "dummy":
                continue
            if s.name not in pps:
                self.logger.info(f"Sink: {s.name}")
                has_sink = True
            if s.name not in rrs:
                self.logger.info(f"Source: {s.name}")
                has_source = True

        if has_sink:
            self.logger.warning("Sink detected")
        if has_source:
            self.logger.warning("Source detected")

        if (has_sink or has_source) and errors:
            sys.exit()

    # ****************
    def check_recombinations(self, errors):
        has_errors = False
        for sp in self.species:
            if sp.charge == 0:
                continue

            if sp.charge > 0:
                electron_recombination_found = False
                # grain_recombination_found = False
                for rea in self.reactions:
                    if sp in rea.reactants and "e-" in [x.name for x in rea.reactants]:
                        electron_recombination_found = True
                    # if sp in rea.reactants and "GRAIN-" in [x.name for x in rea.reactants]:
                    #     grain_recombination_found = True

                    if electron_recombination_found:  # and grain_recombination_found:
                        break

                if not electron_recombination_found:
                    has_errors = True
                    self.logger.warning(f"Electron recombination not found for {sp.name}")
                # if not grain_recombination_found:
                #     print("WARNING: grain recombination not found for %s" % sp.name)

        if has_errors and errors:
            self.logger.error("Recombination errors found")
            sys.exit(1)

    # ****************
    def check_isomers(self, errors):
        has_errors = False
        for i, sp1 in enumerate(self.species):
            for sp2 in self.species[i + 1 :]:
                if sp1.exploded == sp2.exploded:
                    self.logger.warning(f"Isomer detected: {sp1.name} {sp2.name}")
                    has_errors = True

        if has_errors and errors:
            self.logger.error("ERROR: isomer errors found")
            sys.exit(1)

    # ****************
    def check_unique_reactions(self, errors):
        has_duplicates = False
        for i, rea1 in enumerate(self.reactions):
            for rea2 in self.reactions[i + 1 :]:
                if rea1.is_same(rea2):
                    if rea1.tmin != rea2.tmin or rea1.tmax != rea2.tmax:
                        continue
                    if rea1.is_isomer_version(rea2):
                        continue
                    if rea1.guess_type() != rea2.guess_type():
                        continue
                    self.logger.warning(
                        f"Duplicate reaction found: {rea1.get_verbatim()}"
                    )
                    has_duplicates = True

        if has_duplicates and errors:
            self.logger.error("Duplicate reactions found")
            sys.exit(1)

    # ****************
    def generate_reactions_dict(self):
        self.reactions_dict = {
            rea.get_verbatim(): i for i, rea in enumerate(self.reactions)
        }

    # ****************
    def generate_reaction_matrices(self):
        """Generate reaction matrices (rlist and plist) for tracking reactants and products."""
        n_reactions = len(self.reactions)
        n_species = len(self.species)

        # Initialize matrices
        self.rlist = np.zeros((n_reactions, n_species), dtype=int)
        self.plist = np.zeros((n_reactions, n_species), dtype=int)

        # Fill matrices based on reactions
        for i, reaction in enumerate(self.reactions):
            # Count reactants
            for reactant in reaction.reactants:
                species_idx = reactant.index
                self.rlist[i, species_idx] += 1

            # Count products
            for product in reaction.products:
                species_idx = product.index
                self.plist[i, species_idx] += 1

    # ****************
    def get_reaction_verbatim(self, idx):
        return self.reactions[idx].get_verbatim()

    def standardize_symbols(self, expr: Basic, replace_nH: bool):
        """
        This routine applies a set of standard substitution rules to
        standardize symbols.

        Parameters:
            expr : sympy object
                A sympy object on which the standardiation is to be done;
                must support the free_symbols method
            replace_nH : bool
                If True, expressions for the total number density of H and
                He in all chemical states will be replaced with expressions
                in terms of the species number densities; if False, they
                will be changed to the symbols "nh" and "nhe"

        Returns:
            The expression with the substitution rules applied
        """
        if expr == Float(0.0):
            return expr

        nden = MatrixSymbol("nden", len(self.species), 1)
        reps = {}

        def get_element_sum(element):
            terms = []
            for i, spec in enumerate(self.species):
                count = spec.exploded.count(element)
                if count > 0:
                    terms.append(count * nden[Idx(i)])

            return sum(terms) if terms else None

        simple_map = {
            "nh0": "H",
            "nh2": "H2",
            "ne": "e-",
            "nhp": "H+",
        }

        # Suffix mapping for the "n_" logic
        # Symbols of the form "n_"
        # Xp --> X+
        # X0 --> X
        # Xm --> X-
        # e --> e-
        # H --> sum over all H species
        # He --> sum over all He species
        n_suffixes = {"p": "+", "m": "-", "0": ""}

        for fs in expr.free_symbols:
            name = str(fs)
            low_name = name.lower()
            repl = None

            # Handle special "ntot" (sum of all particles)
            if low_name == "ntot":
                repl = sum(nden[Idx(i)] for i in range(len(self.species)))

            # Handle "nh" specifically
            elif low_name == "nh":
                repl = get_element_sum("H") if replace_nH else symbols("nh")

            # Handle simple aliases (nh0, ne, etc)
            elif low_name in simple_map:
                spec_name = simple_map[low_name]
                repl = nden[Idx(self.species_dict[spec_name])]

            # Handle "n_" prefixed symbols
            elif low_name.startswith("n_"):
                core = name[2:]

                # Sub-case: Element sums
                if core in ["H", "He"]:
                    if replace_nH:
                        repl = get_element_sum(core)
                    else:
                        repl = symbols(f"n{core.lower()}")

                # Specific species with suffixes
                else:
                    # Convert suffixes: Xp -> X+, Xm -> X-, X0 -> X, e -> e-
                    if core == "e":
                        core = "e-"
                    elif core[-1] in n_suffixes:
                        core = core[:-1] + n_suffixes[core[-1]]

                    if core in self.species_dict:
                        repl = nden[Idx(self.species_dict[core])]

            # Add valid replacemnts ro the dictionary
            if repl is not None:
                reps[fs] = repl

        return expr.xreplace(reps)

    # *****************
    def get_number_of_species(self):
        return len(self.species)

    # *****************
    def get_species_index(self, name):
        return self.species_dict[name]

    # *****************
    def get_species_object(self, name):
        return self.species[self.species_dict[name]]

    # *****************
    def get_reaction_index(self, name):
        return self.reactions_dict[name]

    # *****************
    def get_latex(self, name, dollars=True):
        for sp in self.species:
            if sp.name == name:
                if dollars:
                    return f"${sp.latex}$"
                else:
                    return sp.latex

        self.logger.error(f"Species {name} latex not found")
        sys.exit(1)

    # *****************
    def get_species_by_serialized(self, serialized):
        for sp in self.species:
            if sp.serialized == serialized:
                return sp
        self.logger.error(f"Species with serialized {serialized} not found")
        sys.exit(1)

    # *****************
    def get_reaction_by_serialized(self, serialized):
        for sp in self.reactions:
            if sp.serialized == serialized:
                return sp
        self.logger.error(f"Reaction with serialized {serialized} not found")
        sys.exit(1)

    # *****************
    def get_reaction_by_verbatim(self, verbatim, rtype=None):
        for rea in self.reactions:
            if rea.get_verbatim() == verbatim:
                if rtype is None or rea.guess_type() == rtype:
                    return rea
        self.logger.error(f"Reaction with verbatim '{verbatim}' not found")
        sys.exit(1)

    # *****************
    def get_table(
        self,
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

        # Get min and max temperature if not provided
        if T_min is None:
            T_min = np.nanmin(
                [r.tmin if r.tmin is not None else np.nan for r in self.reactions]
            )
        if T_max is None:
            T_max = np.nanmax(
                [r.tmax if r.tmax is not None else np.nan for r in self.reactions]
            )
        if T_min is None or T_max is None:
            raise ValueError(
                "could not determine T_min or T_max from "
                "reaction list; set T_min and T_max manually"
            )

        # First step: for each reaction, create a sympy object we can
        # use to substitute to get an expression in terms of the
        # primitive variables
        react_sympy = [r.get_sympy() for r in self.reactions]

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
                logr = sympy.expand_log(sympy.log(r))
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
                    self.logger.info(
                        f"nTemp = {nTemp}, max_err = {max_err} in reaction "
                        f"{self.reactions[idx_max[0]].get_verbatim()} at T = {temp[idx_max[1]]}"
                    )

                # Check for convergence
                if max_err < err_tol:
                    break

        # Return final table
        return temp, np.exp(log_rates)

    def get_sfluxes(self) -> list[sympy.Expr]:
        nspec = len(self.species)
        nreact = len(self.reactions)
        fluxes: list[sympy.Expr] = [sympy.Integer(0) for _ in range(nreact)]
        nden_matrix = MatrixSymbol("nden", nspec, 1)

        for i, reaction in enumerate(self.reactions):
            flux = reaction.rate
            for reactant in reaction.reactants:
                flux *= nden_matrix[self.species_dict[str(reactant)]]

            fluxes[i] = flux

        return fluxes

    def get_sodes(self) -> list[sympy.Basic]:
        nspec = len(self.species)
        fluxes = self.get_sfluxes()
        sodes: list[sympy.Basic] = [sympy.Integer(0) for _ in range(nspec)]

        for i, reaction in enumerate(self.reactions):
            for rr in reaction.reactants:
                idx = (
                    rr.index
                    if isinstance(rr.fidx, str) and rr.fidx.startswith("idx_")
                    else int(rr.fidx)
                )
                sodes[idx] -= fluxes[i]

            # Add flux to products
            for pp in reaction.products:
                idx = (
                    pp.index
                    if isinstance(pp.fidx, str) and pp.fidx.startswith("idx_")
                    else int(pp.fidx)
                )
                sodes[idx] += fluxes[i]

        return sodes

    def get_sradodes(self, order: int = 0) -> list[sympy.Expr]:
        # Check if radiation is enabled
        if self.radiation is None:
            raise RuntimeError(
                "No radiation bands found. Radiation odes cannot be generated"
            )

        # Raise if order is not supported
        if order not in [0, 1, 2, 3]:
            raise ValueError("Invalid order: Supported orders are 0, 1, 2, 3")

        rad_groups = self.radiation.groups
        nden = sympy.MatrixSymbol("nden", len(self.species), 1)

        den = sympy.MatrixSymbol(
            "radeden" if self.radiation.energy_density else "photden",
            self.radiation.nbands,
            1,
        )
        rflux = sympy.MatrixSymbol("rflux", self.radiation.nbands, 1)
        flux_map = {
            den[sympy.Idx(i)]: rflux[sympy.Idx(i)] for i in range(self.radiation.nbands)
        }
        grate, gflux = (
            [sympy.Float(0.0)] * self.radiation.nbands,
            [sympy.Float(0.0)] * self.radiation.nbands,
        )

        for group in rad_groups:
            group_rate: sympy.Basic = sympy.Float(0.0)
            group_dRad_dt_extra = sympy.Float(0.0)
            for reaction, props in group.props.items():
                rrate = props["k"]
                group_dRad_dt_extra += props["delta_rad"]
                for reactant in reaction.reactants:
                    rrate *= nden[sympy.Idx(self.species_dict[str(reactant)])]

                group_rate -= rrate

            # Flux
            flux = group_rate.xreplace(flux_map)
            # dRad_dt_extra assumed to be in units of energy density rate
            group_rate += group_dRad_dt_extra / (
                1 if self.radiation.energy_density else (group.eavg or 1)
            )

            grate[group.index] = group_rate
            gflux[group.index] = flux

        radodes: list[sympy.Expr] = [
            sympy.Float(0.0) for _ in range(2 * self.radiation.nbands)
        ]

        for i, (rate, flux) in enumerate(zip(grate, gflux)):
            ei, fi = self.radiation.ordered_index(i, order)
            radodes[ei] = rate
            radodes[fi] = flux

        return radodes

    # *****************
    def write_table(
        self,
        fname,
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
                rataes above rate_max are clipped to rate_max to prevent
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

        # Deduce output format
        if format == "txt":
            out_type = "txt"
        elif format == "hdf5":
            out_type = "hdf5"
        elif format == "auto":
            if os.path.splitext(fname)[1] == ".txt":
                out_type = "txt"
            elif (
                os.path.splitext(fname)[1] == ".hdf5"
                or os.path.splitext(fname)[1] == ".hdf"
            ):
                out_type = "hdf5"
            else:
                raise ValueError(
                    "cannot deduce output type from extension {:s}".format(
                        os.path.splitext(fname)
                    )
                )
        else:
            raise ValueError("unknown output format {:s}".format(str(format)))

        # Get rate coefficients
        temp, coef = self.get_table(
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
            if self.reactions[i].guess_type() == "unknown":
                rtype.append("2_body")
            else:
                rtype.append(self.reactions[i].guess_type())
            reactants_ = {}
            for r in self.reactions[i].reactants:
                if r.name in reactants_.keys():
                    reactants_[r.name] += 1
                else:
                    reactants_[r.name] = 1
            reactants.append(reactants_)
            products_ = {}
            for p in self.reactions[i].products:
                if p.name in products_.keys():
                    products_[p.name] += 1
                else:
                    products_[p.name] = 1
            products.append(products_)

        # Write output in appropriate format
        if out_type == "txt":
            # Text output
            fp = open(fname, "w")

            # Write header
            fp.write("# JAFF auto-generated rate coefficient table\n")
            fp.write("# Network name: {:s}\n".format(self.label))
            fp.write("# Reactions included\n")
            fp.write("#   (reactants) (products) (reaction type)\n")
            for rt, r, p in zip(rtype, reactants, products):
                fp.write("#   {:s} {:s} {:s}\n".format(repr(r), repr(p), rt))

            # Write data in quokka table format
            fp.write("1\n")  # Table is 1d
            fp.write("{:d}\n".format(len(coef)))  # N outputs per table entry
            if fast_log:
                fp.write("3\n")  # Table is uniform in fast_log
            else:
                fp.write("2\n")  # Table is uniform in log
            fp.write("{:d}\n".format(len(temp)))  # Number of temperature entries
            fp.write("{:e} {:e}\n".format(temp[0], temp[-1]))  # Min/max temperature

            # Now write the data
            for c in coef:
                for c_ in c:
                    fp.write("{:e} ".format(c_))
                fp.write("\n")

            # Close
            fp.close()

        elif out_type == "hdf5":
            # HDF5 output
            fp = h5py.File(fname, mode="w")

            # Create a group to contain the data
            grp = fp.create_group("reaction_coeff")

            # Store metadata in the attributes
            grp.attrs["input_names"] = ["temperature"]
            grp.attrs["input_units"] = ["K"]
            grp.attrs["xlo"] = np.array([temp[0]])
            grp.attrs["xhi"] = np.array([temp[-1]])
            if fast_log:  # Spacing type
                grp.attrs["spacing"] = ["fast_log"]
            else:
                grp.attrs["spacing"] = ["log"]

            # Store information on which reactions / rate coefficients
            # are included; note that we store these as data sets
            # instead of attributes to avoid problems in the case where
            # the number of reactions is very large, and thus resulting
            # size of the output reaction list exceeds the HDF5 limit
            # on the sizes of attributes
            output_names = []
            output_units = []
            for i, rt, r, p in zip(range(len(rtype)), rtype, reactants, products):
                output_names.append(
                    "{:s} rate coefficient: {:s} --> {:s}".format(str(rt), str(r), str(p))
                )
                output_units.append("cm^3 s^-1")
            grp.create_dataset(
                "output_names", data=output_names, dtype=h5py.string_dtype()
            )
            grp.create_dataset(
                "output_units", data=output_units, dtype=h5py.string_dtype()
            )

            # Create data set holding the coefficient table
            grp.create_dataset("data", data=coef)

            # Close file
            fp.close()
