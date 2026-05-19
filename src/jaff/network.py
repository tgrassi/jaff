from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import NotRequired, TypedDict

import numpy as np
from sympy import (
    Basic,
    Expr,
    Float,
    Function,
    Idx,
    MatrixSymbol,
    Max,
    Min,
    parse_expr,
    symbols,
)
from sympy.core.function import AppliedUndef, UndefinedFunction

from .auxilary_file_parser import AuxilaryFunctionParser, FunctionsDict
from .common import is_jaff_file
from .common.helper import load_mass_dict, resolve_dependencies
from .common.welcome import motd
from .core.io import JaffProps, from_jaff_file, to_jaff_file, write_data_table
from .core.logger import JaffLogger, jaff_progress
from .errors import ParserError
from .network_parser import NetworkParser
from .photochemistry import Photochemistry
from .physics import constants
from .physics.equations import get_sfluxes, get_sodes, get_sradodes
from .physics.radiation import Radiation
from .reaction import Reaction
from .species import Species

NetworkProps = TypedDict(
    "NetworkProps",
    {
        "fname": str | Path,
        "errors": NotRequired[bool],
        "label": NotRequired[str],
        "funcfile": NotRequired[str],
        "replace_nH": NotRequired[bool],
        "rad_bands": NotRequired[list],
        "rad_powerlaw_index": NotRequired[int | float],
        "rad_energy_density": NotRequired[bool],
        "c": NotRequired[float],
        "_from_cli": NotRequired[bool],
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
    def __init__(
        self,
        fname: str | Path,
        errors: bool = False,
        label: str | None = None,
        funcfile: str | Path | None = None,
        replace_nH: bool = True,
        rad_bands: list[str | int | float | Basic] = [],
        rad_powerlaw_index: int | float = 0,
        rad_energy_density: bool = False,
        c: float = constants.cgs.c,  # Speed of light in cgs unit
        _from_cli: bool = False,
    ):
        self.logger: logging.Logger = JaffLogger().get_logger()

        if isinstance(fname, str):
            fname = Path(fname)

        fname = fname.resolve()
        if not fname.exists():
            raise FileNotFoundError(fname)

        jaff_props: JaffProps = {}
        loaded_from_jaff_file = is_jaff_file(fname)
        if loaded_from_jaff_file:
            jaff_props = from_jaff_file(fname, errors)

        self.file_name: Path = jaff_props.get("file_name", fname)
        self.label = jaff_props.get("label", label or self.file_name.stem)
        if not _from_cli:
            print(motd())

        self.mass_dict: dict[str, ElementProps] = {}
        self.species: list[Species] = []
        self.specie_index: dict[str, int] = {}
        self.reactions: list[Reaction] = []
        self.reaction_index: dict[str, int] = {}
        self.rlist: np.ndarray | None = None
        self.plist: np.ndarray | None = None
        self.dEdt_chem: Basic = Float(0.0)
        self.dEdt_other: Basic = Float(0.0)
        self.dRad_dt_extra: Basic = Float(0.0)
        self.radiation: Radiation | None = (
            Radiation(rad_bands, rad_powerlaw_index, rad_energy_density, c)
            if len(rad_bands) > 0
            else None
        )

        self.logger.info(f"Loading network from {fname}")
        self.logger.info(f"Network label: [yellow]{self.label}[/]")

        self.mass_dict = load_mass_dict()
        self.photochemistry = Photochemistry()

        if not loaded_from_jaff_file:
            self.__load_network(fname, funcfile, replace_nH)
        else:
            self.__load_network_from_jaff_file(jaff_props)
        self.__normalize_nework_extras(replace_nH)

        self.check_sink_sources(errors)
        self.check_recombinations(errors)
        self.check_isomers(errors)
        self.check_unique_reactions(errors)

        self.__generate_reactions_dict()
        self.generate_reaction_matrices()

        self.logger.info("[green]Network loaded successfully![/]")

    def __load_network(
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
        aux_funcs = self.__read_aux_funcs(funcfile)

        global_vars = {
            var: resolve_dependencies(expr, {}, aux_funcs)
            for var, expr in global_vars.items()
        }
        subs_dict: dict[Basic, Basic] = {
            symbols(var.lower()): expr for var, expr in global_vars.items()
        }

        for i, reaction in enumerate(
            jaff_progress.track(
                reactions_list,
                description=f"Creating {self.label} network",
            )
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
                    self.specie_index[s] = self.species[-1].index
                    self.specie_index[self.species[-1].serialized] = self.species[
                        -1
                    ].index

            rr = [self.species[self.specie_index[r]] for r in reactants]
            pp = [self.species[self.specie_index[p]] for p in products]

            local_subs_dict = {**subs_dict}

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

            # Handle rate
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
                    rea.custom_rad_rate = True
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
            self.dEdt_other = self.__standardize_symbols(self.dEdt_other, replace_nH)
            free_symbols |= self.free_symbols(self.dEdt_other)
            self.__detect_undefined_functions(self.dEdt_other, undef_funcs, interp_funcs)

        self.logger.info(
            f"Variables found: {', '.join(sorted(f'[cyan]{s}[/]' for s in free_symbols))}"
        )
        self.logger.info(f"Loaded {len(self.reactions)} reactions")
        self.logger.info(f"Loaded {n_photo} photo-chemistry reactions")

        # Issue warning message if undefined functions remain
        if interp_funcs:
            self.logger.info(
                f"Found the following interpolation functions: {', '.join([f'[cyan]{func}[/]' for func in interp_funcs])}"
            )
        if undef_funcs:
            self.logger.warning(
                f"Found undefined functions {', '.join([f'[red]{func}[/]' for func in undef_funcs])}"
            )

    def __load_network_from_jaff_file(self, jaff_props: JaffProps):
        self.species = jaff_props["species"]
        self.specie_index = jaff_props["specie_index"]
        for reaction in jaff_props["reactions"]:
            rea = Reaction(
                reactants=reaction["reactants"],
                products=reaction["products"],
                rate=reaction["rate"],
                dE=reaction["dE"],
                dRad_dt=reaction["dRad_dt"],
                tmin=reaction["tmin"],
                tmax=reaction["tmax"],
                original_string=reaction["original_string"],
            )
            rea.xsecs_dict = reaction["xsecs_dict"]
            rea.custom_rad_rate = reaction["custom_rad_rate"]
            self.reactions.append(rea)

            if rea.guess_type() == "photo" and self.radiation is not None:
                if rea.custom_rad_rate:
                    self.radiation.set_custom_rate(rea)
                    continue

                self.radiation.set_custom_rate(rea)

    def __normalize_nework_extras(self, replace_nH):
        # Apply replacement rules to replace standard symbols
        # appearing in rates with terms involving known species
        nden = MatrixSymbol("nden", len(self.species), 1)
        for r in self.reactions:
            r.rate = self.__standardize_symbols(r.rate, replace_nH)

            dE_dt = r.dE * r.rate  # type: ignore
            for s in r.reactants:
                dE_dt *= nden[self.specie_index[s.name]]
            self.dEdt_chem += dE_dt
            self.dRad_dt_extra += r.dRad_dt  # type: ignore
        self.dEdt_chem = self.__standardize_symbols(self.dEdt_chem, replace_nH)
        self.dRad_dt_extra = self.__standardize_symbols(self.dRad_dt_extra, replace_nH)

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
        expr: Expr | Basic, undef_funcs: set, interp_funcs: set
    ) -> None:
        for f in expr.atoms(AppliedUndef):
            if "interp" in f.func.__name__:
                interp_funcs |= {f.func.__name__}
                continue
            undef_funcs |= {f.func.__name__}

    def __read_aux_funcs(self, funcfile: str | Path | None) -> dict:
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
            raise FileNotFoundError(funcfile)

        with AuxilaryFunctionParser(funcfile) as afp:
            func_dict: FunctionsDict = afp.get_dict()

        return func_dict

    def to_jaff(self, filename: str | Path):
        to_jaff_file(filename, self)

    @staticmethod
    def free_symbols(expr: Basic) -> set[Basic]:
        return {fs for fs in expr.free_symbols if "nden" not in str(fs)}

    def compare_reactions(self, other: Network, verbosity: int = 1):
        self.logger.info(f'Comparing networks "{self.label}" and "{other.label}"...')

        self_reacts = {rea.serialized for rea in self.reactions}
        other_reacts = {rea.serialized for rea in other.reactions}

        common = self_reacts & other_reacts
        not_in_self = other_reacts - common
        not_in_other = self_reacts - common

        if verbosity == 1:
            self.logger.info(f"Reactions not present in {self.label}:")
            print(
                "\n".join(
                    [str(other.get_reaction_by_serialized(rea)) for rea in not_in_self]
                ),
                "\n",
            )

            self.logger.info(f"Reactions not present in {other.label}:")
            print(
                "\n".join(
                    [str(self.get_reaction_by_serialized(rea)) for rea in not_in_other]
                ),
                "\n",
            )

            self.logger.info(f"Reactions present in both {self.label} and {other.label}:")
            print(
                "\n".join([str(self.get_reaction_by_serialized(rea)) for rea in common]),
                "\n",
            )

        self.logger.info(f"{len(common)} reactions are common in both networks")
        self.logger.info(f'{len(not_in_self)} reactions are missing in "{self.label}"')
        self.logger.info(f'{len(not_in_other)} reactions are missing in "{other.label}"')

    def compare_species(self, other: Network, verbosity: int = 1) -> None:
        self.logger.info(
            f'Comparing species in networks "{self.label}" and "{other.label}"...'
        )

        self_species = {sp.serialized for sp in self.species}
        other_species = {sp.serialized for sp in other.species}

        common = self_species & other_species
        not_in_self = other_species - common
        not_in_other = self_species - common

        if verbosity == 1:
            self.logger.info(f"Species not present in {self.label}:")
            print(
                ", ".join(
                    [str(other.get_species_by_serialized(sp)) for sp in not_in_self]
                ),
                "\n",
            )

            self.logger.info(f"Species not present in {other.label}:")
            print(
                ", ".join(
                    [str(self.get_species_by_serialized(sp)) for sp in not_in_other]
                ),
                "\n",
            )

            self.logger.info(f"Species present in both {self.label} and {other.label}:")
            print(
                ", ".join([str(self.get_species_by_serialized(sp)) for sp in common]),
                "\n",
            )

        self.logger.info(f"{len(common)} species are common in both networks")
        self.logger.info(f'{len(not_in_self)} species are missing in "{self.label}"')
        self.logger.info(f'{len(not_in_other)} species are missing in "{other.label}"')

    def check_sink_sources(self, errors: bool) -> None:
        produced = {p.name for rea in self.reactions for p in rea.products}
        consumed = {r.name for rea in self.reactions for r in rea.reactants}
        species_names = {s.name for s in self.species if s.name != "dummy"}

        sinks = species_names - produced
        sources = species_names - consumed

        for name in sinks:
            self.logger.info(f"Sink: [cyan]{name}[/]")

        for name in sources:
            self.logger.info(f"Source: [cyan]{name}[/]")

        if sinks:
            self.logger.warning("Sink detected")

        if sources:
            self.logger.warning("Source detected")

        if (sinks or sources) and errors:
            self.logger.error("Exiting since errors are enabled")
            sys.exit()

    def check_recombinations(self, errors: bool) -> None:
        electron_recomb_species = set()

        for rea in self.reactions:
            reactant_names = {r.name for r in rea.reactants}

            if "e-" in reactant_names:
                for r in rea.reactants:
                    if r.name != "e-":
                        electron_recomb_species.add(r.name)

        has_errors = False

        for sp in self.species:
            if sp.charge <= 0:
                continue

            if sp.name not in electron_recomb_species:
                has_errors = True
                self.logger.warning(
                    f"Electron recombination not found for [cyan]{sp.name}[/]"
                )

        if has_errors and errors:
            self.logger.error("Recombination errors found")
            sys.exit(1)

    def check_isomers(self, errors: bool) -> None:
        groups = {}

        for sp in self.species:
            key = tuple(sp.exploded)
            groups.setdefault(key, []).append(f"[cyan]{sp.name}[/]")

        has_errors = False

        for exploded, names in groups.items():
            if len(names) > 1:
                has_errors = True
                self.logger.warning(f"Isomers detected: {', '.join(names)}")

        if has_errors and errors:
            self.logger.error("Isomer errors found")
            sys.exit(1)

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
                        f"Duplicate reaction found: [cyan]{rea1.get_verbatim()}[/]"
                    )
                    has_duplicates = True

        if has_duplicates and errors:
            self.logger.error("Duplicate reactions found")
            sys.exit(1)

    def __generate_reactions_dict(self) -> None:
        for i, rea in enumerate(self.reactions):
            self.reaction_index[rea.verbatim] = i
            self.reaction_index[rea.serialized] = i

    def generate_reaction_matrices(self) -> None:
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

    def get_reaction_verbatim(self, idx: int) -> str:
        return self.reactions[idx].verbatim

    def __standardize_symbols(self, expr: Basic, replace_nH: bool) -> Basic:
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
                repl = nden[Idx(self.specie_index[spec_name])]

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

                    if core in self.specie_index:
                        repl = nden[Idx(self.specie_index[core])]

            # Add valid replacemnts ro the dictionary
            if repl is not None:
                reps[fs] = repl

        return expr.xreplace(reps)

    def get_number_of_species(self) -> int:
        return len(self.species)

    def get_number_of_reactions(self) -> int:
        return len(self.reactions)

    def get_species_index(self, name: str) -> int:
        return self.specie_index[name]

    def get_species_object(self, name) -> Species:
        return self.species[self.specie_index[name]]

    def get_reaction_index(self, name) -> int:
        return self.reaction_index[name]

    def get_latex(self, name: str, dollars: bool = True) -> str:
        if name not in self.specie_index:
            raise KeyError(f"Invalid specie name: {name}")

        sp = self.species[self.specie_index[name]]
        return f"${sp.latex}$" if dollars else sp.latex

    def get_species_by_serialized(self, serialized: str) -> Species:
        if serialized not in self.specie_index:
            raise KeyError(f"Invalid serealized specie: {serialized}")

        return self.species[self.specie_index[serialized]]

    def get_reaction_by_serialized(self, serialized: str) -> Reaction:
        if serialized not in self.reaction_index:
            raise KeyError(f"Invalid serealized reaction: {serialized}")

        return self.reactions[self.reaction_index[serialized]]

    def get_reaction_by_verbatim(
        self, verbatim: str, rtype: str | None = None
    ) -> Reaction | None:
        if verbatim not in self.reaction_index:
            raise KeyError(f"Invalid verbatim reaction: {verbatim}")

        rea = self.reactions[self.reaction_index[verbatim]]
        if rtype is None or rea.guess_type() == rtype:
            return rea

    def sfluxes(self) -> list[Expr]:
        return get_sfluxes(self.reactions, self.specie_index)

    def sodes(self) -> list[Basic]:
        return get_sodes(self.reactions, self.specie_index)

    def sradodes(self, order: int = 0) -> list[Expr]:
        return get_sradodes(self.radiation, self.specie_index, order)

    def to_hdf5(
        self,
        fname: str | Path,
        label: str | None = None,
        T_min=None,
        T_max=None,
        nT=64,
        err_tol=0.01,
        rate_min=1e-30,
        rate_max=1e100,
        fast_log=False,
        include_all=False,
        verbose=False,
    ) -> None:
        if isinstance(fname, str):
            fname = Path(fname)

        if fname.suffix not in [".hdf5", ".hdf"]:
            fname.with_suffix(".hdf5")

        write_data_table(
            reactions=self.reactions,
            logger=self.logger,
            fname=fname,
            label=label or self.label,
            T_min=T_min,
            T_max=T_max,
            nT=nT,
            err_tol=err_tol,
            rate_min=rate_min,
            rate_max=rate_max,
            fast_log=fast_log,
            format="hdf5",
            include_all=include_all,
            verbose=verbose,
        )

    def to_txt(
        self,
        fname: str | Path,
        label: str | None = None,
        T_min=None,
        T_max=None,
        nT=64,
        err_tol=0.01,
        rate_min=1e-30,
        rate_max=1e100,
        fast_log=False,
        include_all=False,
        verbose=False,
    ) -> None:
        if isinstance(fname, str):
            fname = Path(fname)

        if fname.suffix != ".txt":
            fname.with_suffix(".txt")

        write_data_table(
            reactions=self.reactions,
            logger=self.logger,
            fname=fname,
            label=label or self.label,
            T_min=T_min,
            T_max=T_max,
            nT=nT,
            err_tol=err_tol,
            rate_min=rate_min,
            rate_max=rate_max,
            fast_log=fast_log,
            format="txt",
            include_all=include_all,
            verbose=verbose,
        )

    def write_table(
        self,
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
    ) -> None:

        write_data_table(
            reactions=self.reactions,
            logger=self.logger,
            fname=fname,
            label=label or self.label,
            T_min=T_min,
            T_max=T_max,
            nT=nT,
            err_tol=err_tol,
            rate_min=rate_min,
            rate_max=rate_max,
            fast_log=fast_log,
            format=format,
            include_all=include_all,
            verbose=verbose,
        )
