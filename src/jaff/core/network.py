"""Top-level ``Network`` class for loading and querying JAFF reaction networks.

A ``Network`` is the main entry point for users of the JAFF library.  It
reads a reaction network file in any supported format (KROME, PRIZMO, UDFA,
KIDA, UCLChem, or the binary ``.jaff`` serialisation), builds typed
``Species`` and ``Reactions`` catalogues, validates the network, and exposes
symbolic ODE and flux expressions for downstream code generation.

Auxiliary ``.jfunc`` files may accompany the network file.  They can supply
custom rate coefficients, chemical heating/cooling rates, and radiation
moment contributions using the ``@var`` / ``@function`` syntax parsed by
``AuxiliaryFunctionParser``.

Number densities are represented as ``nden[i]`` — a reference into a SymPy
``MatrixSymbol("nden", n_species, 1)``.  The symbol ``idx_X`` refers to the
integer position of species ``X`` within the network.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

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

from ..common import is_jaff_file, load_mass_dict, motd, resolve_dependencies
from ..common._helper import ElementProps
from ..errors import ParserError
from ..io import JaffLogger, jaff_progress
from ..io._io import JaffProps, from_jaff_file, to_jaff_file, write_data_table
from ..physics import (
    Photochemistry,
    Radiation,
    constants,
    get_sfluxes,
    get_sodes,
    get_sradodes,
)
from ._auxiliary_engine import AuxiliaryFunctionParser, FunctionsDict
from ._network_engine import NetworkParser
from .elements import Elements
from .reaction import Reaction, Reactions
from .species import Specie, Species


class Network:
    """Astrochemical reaction network loaded from a file.

    After construction the following public attributes are available:

    Attributes
    ----------
    file_name : Path
        Absolute path to the source network file.
    label : str
        Human-readable label for this network (defaults to the file stem).
    species : Species
        Ordered catalogue of all species in the network.
    reactions : Reactions
        Ordered catalogue of all reactions in the network.
    elements : Elements
        Unique elements derived from all species.
    reactant_matrix : np.ndarray
        Integer stoichiometry matrix, shape ``(n_reactions, n_species)``.
        Entry ``[i, j]`` counts how many times species *j* appears as a
        reactant in reaction *i*.
    product_matrix : np.ndarray
        Integer stoichiometry matrix for products, same shape.
    dEdt_chem : Basic
        SymPy expression for the total chemical heating/cooling rate
        (erg cm⁻³ s⁻¹), accumulated over all reactions.
    dEdt_other : Basic
        Additional heating/cooling rate from the ``heatingcoolingrate``
        auxiliary function, if present.
    dRad_dt_extra : Basic
        Extra radiation moment source terms from ``@function`` definitions.
    radiation : Radiation | None
        Radiation field object; ``None`` when no radiation bands are specified.
    photochemistry : Photochemistry
        Cross-section database used to populate ``xsecs_dict`` on photo-reactions.
    mass_dict : dict[str, ElementProps]
        Element mass dictionary used during species construction.
    """

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
        """Load a reaction network from *fname*.

        Parameters
        ----------
        fname : str | Path
            Path to the network file.  Supported extensions: any text format
            auto-detected by ``NetworkParser``, plus ``.jaff`` binary files.
        errors : bool, optional
            If ``True``, treat conservation violations and duplicate reactions
            as fatal errors (process exits).  Default ``False`` (warnings
            only).
        label : str | None, optional
            Human-readable name for this network.  Defaults to the file stem.
        funcfile : str | Path | None, optional
            Path to a ``.jfunc`` auxiliary function file.  When ``None``,
            JAFF looks for ``<network>.jfunc`` in the same directory.  Pass
            the string ``"none"`` to skip auxiliary-function loading entirely.
        replace_nH : bool, optional
            When ``True`` (default), the shorthand symbol ``nh`` (and ``n_H``,
            ``n_He``) in rate expressions is expanded to a sum of
            ``nden[i]`` terms over all H-bearing (He-bearing) species.  Set
            to ``False`` to keep ``nh`` / ``nhe`` as free symbols.
        rad_bands : list, optional
            Radiation band boundaries used to construct the ``Radiation``
            object.  An empty list (default) disables radiation transport.
        rad_powerlaw_index : int | float, optional
            Power-law spectral index for the radiation field, default ``0``.
        rad_energy_density : bool, optional
            If ``True``, radiation moments are energy densities rather than
            number densities, default ``False``.
        c : float, optional
            Speed of light in CGS units (cm s⁻¹).  Defaults to
            ``constants.cgs.c``.
        _from_cli : bool, optional
            Internal flag: suppresses the MOTD banner when ``True``.

        Raises
        ------
        FileNotFoundError
            If *fname* does not exist.
        """
        self.logger: logging.Logger = JaffLogger().get_logger()

        if isinstance(fname, str):
            fname = Path(fname)

        fname = fname.resolve()
        if not fname.exists():
            raise FileNotFoundError(fname)

        jaff_props: JaffProps = {}  # type: ignore
        loaded_from_jaff_file = is_jaff_file(fname)
        if loaded_from_jaff_file:
            jaff_props = from_jaff_file(fname, errors)

        self.file_name: Path = jaff_props.get("file_name", fname)
        self.label = jaff_props.get("label", label or self.file_name.stem)
        if not _from_cli:
            print(motd())

        self.mass_dict: dict[str, ElementProps] = {}
        self.species: Species = Species()
        self.reactions: Reactions = Reactions()
        self.reactant_matrix: np.ndarray | None = None
        self.product_matrix: np.ndarray | None = None
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

        self.mass_dict: dict[str, ElementProps] = load_mass_dict()
        Species.configure(self.mass_dict)
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

        self.__generate_reaction_matrices()

        self.elements: Elements = Elements(self.species._list)

        self.logger.info("[green]Network loaded successfully![/]")

    def __load_network(
        self,
        fname,
        funcfile,
        replace_nH,
    ):
        """Parse the network file and build species, reactions, and auxiliary quantities.

        Parameters
        ----------
        fname : Path
            Resolved path to the network file.
        funcfile : str | Path | None
            Path to an auxiliary ``.jfunc`` file, or ``None``/``"none"`` to skip.
        replace_nH : bool
            When ``True``, expand ``nh`` to a sum over H-bearing species.
        """
        specie_names = set()
        free_symbols = set()
        undef_funcs = set()
        interp_funcs = set()

        n_photo = 0
        tgas = symbols("tgas")

        with NetworkParser(fname, self.logger) as netp:
            reactions_list, global_vars = netp.get_parsed()

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

            for s in reactants + products:
                if s not in specie_names:
                    specie_names.add(s)
                    self.species.add(Specie(s, len(specie_names) - 1))

            rr = [self.species[r] for r in reactants]
            pp = [self.species[p] for p in products]

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

            rate_expr, is_photoreaction, n_photo = self.__parse_rate(
                aux_chem_rate, rate, aux_funcs, global_vars, n_photo
            )
            rate_expr = resolve_dependencies(rate_expr, local_subs_dict, aux_funcs)

            # deltarad{i}: photon absorption/emission rate per band for the moment-0 equations
            deltaRad: Basic = Float(0.0)
            if aux_delta_rad in aux_funcs:
                deltaRad = aux_funcs[aux_delta_rad]["def"]

            # deltae{i}: chemical energy change per reaction, accumulates into dEdt_chem
            deltaE: Basic = Float(0.0)
            if aux_delta_e in aux_funcs:
                deltaE = aux_funcs[aux_delta_e]["def"]

            for expr in [rate_expr, deltaE, deltaRad]:
                free_symbols |= self.free_symbols(expr)
                self.__detect_undefined_functions(expr, undef_funcs, interp_funcs)

            rea = Reaction(
                rr, pp, rate_expr, tmin, tmax, deltaE, deltaRad, reaction["string"], i
            )
            self.reactions.add(rea)

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

            if rea.rtype() == "photo":
                rea.xsecs_dict = self.photochemistry.get_xsec(rea)

        if "heatingcoolingrate" in aux_funcs:
            self.dEdt_other = aux_funcs["heatingcoolingrate"]["def"]
            self.dEdt_other = self.__standardize_symbols(self.dEdt_other, replace_nH)
            free_symbols |= self.free_symbols(self.dEdt_other)
            self.__detect_undefined_functions(self.dEdt_other, undef_funcs, interp_funcs)

        self.logger.info(
            f"Variables found: {', '.join(sorted(f'[cyan]{s}[/]' for s in free_symbols))}"
        )
        self.logger.info(f"Loaded {self.reactions.count} reactions")
        self.logger.info(f"Loaded {n_photo} photo-chemistry reactions")

        if interp_funcs:
            self.logger.info(
                f"Found the following interpolation functions: {', '.join([f'[cyan]{func}[/]' for func in interp_funcs])}"
            )
        if undef_funcs:
            self.logger.warning(
                f"Found undefined functions {', '.join([f'[red]{func}[/]' for func in undef_funcs])}"
            )

    def __load_network_from_jaff_file(self, jaff_props: JaffProps):
        """Restore species, reactions, and radiation state from a ``.jaff`` file payload.

        Parameters
        ----------
        jaff_props : JaffProps
            Deserialised property dictionary returned by
            :func:`~jaff.io._io.from_jaff_file`.
        """
        self.species = jaff_props["species"]
        for i, reaction in enumerate(jaff_props["reactions"]):
            rea = Reaction(
                reactants=reaction["reactants"],
                products=reaction["products"],
                rate=reaction["rate"],
                dE=reaction["dE"],
                dRad=reaction["dRad"],
                tmin=reaction["tmin"],
                tmax=reaction["tmax"],
                original_string=reaction["original_string"],
                index=i,
            )
            rea.xsecs_dict = reaction["xsecs_dict"]
            rea.custom_rad_rate = reaction["custom_rad_rate"]
            self.reactions.add(rea)

            if rea.rtype() == "photo" and self.radiation is not None:
                if rea.custom_rad_rate:
                    self.radiation.set_custom_rate(rea)
                    continue

                self.radiation.set_custom_rate(rea)

    def __normalize_nework_extras(self, replace_nH):
        """Standardize convenience symbols in all rate and auxiliary expressions.

        Replaces shorthand symbols (``nh``, ``ne``, ``ntot``, ``n_X``, …) with
        ``nden[i]`` references in every reaction rate, the chemical heating/cooling
        sum :attr:`dEdt_chem`, and the extra radiation source term
        :attr:`dRad_dt_extra`.

        Parameters
        ----------
        replace_nH : bool
            When ``True``, expand hydrogen-density shorthands to sums over
            H-bearing species.
        """
        nden = MatrixSymbol("nden", self.species.count, 1)
        for r in self.reactions:
            r.rate = self.__standardize_symbols(r.rate, replace_nH)

            dE_dt = r.dE * r.rate  # type: ignore
            for s in r.reactants:
                dE_dt *= nden[self.species[s.name].index]
            self.dEdt_chem += dE_dt
            self.dRad_dt_extra += r.dRad  # type: ignore
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
        """Convert a raw rate string to a SymPy expression.

        Checks, in priority order:

        1. Whether an auxiliary function named *aux_chem_rate* exists (custom rate).
        2. Whether *rate* is a global variable name.
        3. Whether *rate* describes a photo-reaction (contains ``"photo"``).
        4. Falls back to ``sympy.parse_expr``.

        Parameters
        ----------
        aux_chem_rate : str
            Key for the optional custom-rate auxiliary function (e.g. ``"chemrate0"``).
        rate : str
            Raw rate string from the network file.
        aux_funcs : dict[str, FunctionsDict]
            Parsed auxiliary functions dictionary.
        global_vars : dict[str, Basic]
            Resolved global variable map from the network file.
        n_photo : int
            Running counter of photo-reactions seen so far.

        Returns
        -------
        tuple[Basic, bool, int]
            ``(rate_expr, is_photoreaction, n_photo)`` where *n_photo* is
            incremented by 1 for photo-reactions.
        """
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
        """Scan *expr* for undefined function calls and categorise them.

        Functions whose names contain ``"interp"`` are added to *interp_funcs*;
        all others are added to *undef_funcs*.

        Parameters
        ----------
        expr : Expr | Basic
            SymPy expression to scan.
        undef_funcs : set
            Accumulator for unrecognised undefined function names.
        interp_funcs : set
            Accumulator for interpolation function names.
        """
        for f in expr.atoms(AppliedUndef):
            if "interp" in f.func.__name__:
                interp_funcs |= {f.func.__name__}
                continue
            undef_funcs |= {f.func.__name__}

    def __read_aux_funcs(self, funcfile: str | Path | None) -> dict:
        """Load auxiliary function file (.jfunc).

        If funcfile is None, looks for <network_name>.jfunc alongside the network file.
        Pass ``"none"`` to skip loading entirely.
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

        with AuxiliaryFunctionParser(funcfile) as afp:
            func_dict: FunctionsDict = afp.get_dict()

        return func_dict

    def to_jaff(self, filename: str | Path):
        """Serialise this network to a binary ``.jaff`` file.

        Parameters
        ----------
        filename : str | Path
            Output file path.  The ``.jaff`` extension is conventional but
            not enforced.
        """
        to_jaff_file(filename, self)

    @staticmethod
    def free_symbols(expr: Basic) -> set[Basic]:
        """Return the free symbols of *expr*, excluding ``nden`` matrix entries.

        ``nden[i]`` references are excluded because they are internal index
        variables, not user-visible physical symbols.

        Parameters
        ----------
        expr : Basic
            A SymPy expression.

        Returns
        -------
        set[Basic]
            Free symbols that do not involve ``"nden"``.
        """
        return {fs for fs in expr.free_symbols if "nden" not in str(fs)}

    def compare_reactions(self, other: Network, verbosity: int = 1):
        """Log reactions present in one network but not the other.

        Parameters
        ----------
        other : Network
            Network to compare against.
        verbosity : int, optional
            When ``1`` (default), print the reaction sets for common and
            unique reactions.  Other values suppress output.
        """
        self.logger.info(f'Comparing networks "{self.label}" and "{other.label}"...')

        self_reacts = {rea.serialized for rea in self.reactions}
        other_reacts = {rea.serialized for rea in other.reactions}

        common = self_reacts & other_reacts
        not_in_self = other_reacts - common
        not_in_other = self_reacts - common

        if verbosity == 1:
            self.logger.info(f"Reactions not present in {self.label}:")
            print(
                "\n".join([str(other.reactions[rea]) for rea in not_in_self]),
                "\n",
            )

            self.logger.info(f"Reactions not present in {other.label}:")
            print(
                "\n".join([str(self.reactions[rea]) for rea in not_in_other]),
                "\n",
            )

            self.logger.info(f"Reactions present in both {self.label} and {other.label}:")
            print(
                "\n".join([str(self.reactions[rea]) for rea in common]),
                "\n",
            )

        self.logger.info(f"{len(common)} reactions are common in both networks")
        self.logger.info(f'{len(not_in_self)} reactions are missing in "{self.label}"')
        self.logger.info(f'{len(not_in_other)} reactions are missing in "{other.label}"')

    def compare_species(self, other: Network, verbosity: int = 1) -> None:
        """Log species present in one network but not the other.

        Parameters
        ----------
        other : Network
            Network to compare against.
        verbosity : int, optional
            When ``1`` (default), print the species sets.
        """
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
                ", ".join([str(other.species[sp]) for sp in not_in_self]),
                "\n",
            )

            self.logger.info(f"Species not present in {other.label}:")
            print(
                ", ".join([str(self.species[sp]) for sp in not_in_other]),
                "\n",
            )

            self.logger.info(f"Species present in both {self.label} and {other.label}:")
            print(
                ", ".join([str(self.species[sp]) for sp in common]),
                "\n",
            )

        self.logger.info(f"{len(common)} species are common in both networks")
        self.logger.info(f'{len(not_in_self)} species are missing in "{self.label}"')
        self.logger.info(f'{len(not_in_other)} species are missing in "{other.label}"')

    def check_sink_sources(self, errors: bool) -> None:
        """Warn (or abort) if any species is never produced or never consumed.

        A *sink* species appears as a reactant in at least one reaction but
        is never produced.  A *source* species is produced but never consumed.
        The special species ``"dummy"`` is excluded from the check.

        Parameters
        ----------
        errors : bool
            If ``True``, call ``sys.exit()`` when sinks or sources are found.
        """
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
        """Warn if any positively charged species has no electron recombination reaction.

        Parameters
        ----------
        errors : bool
            If ``True``, call ``sys.exit(1)`` when recombination reactions
            are missing.
        """
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
        """Warn if two or more species share the same atomic composition (isomers).

        Isomers are detected by comparing ``Specie.exploded`` tuples.  For
        example, HCO+ and HOC+ both have ``["C", "H", "O", "+"]`` and would
        be reported here.

        Parameters
        ----------
        errors : bool
            If ``True``, call ``sys.exit(1)`` when isomers are found.
        """
        groups = {}

        for sp in self.species:
            key = tuple(sp.exploded)
            groups.setdefault(key, []).append(f"[cyan]{sp.name}[/]")

        has_errors = False

        for _, names in groups.items():
            if len(names) > 1:
                has_errors = True
                self.logger.warning(f"Isomers detected: {', '.join(names)}")

        if has_errors and errors:
            self.logger.error("Isomer errors found")
            sys.exit(1)

    def check_unique_reactions(self, errors):
        """Warn if duplicate reactions (same species, same type, same T range) are found.

        Two reactions are considered true duplicates when their serialized
        forms match, their temperature ranges overlap, they have the same
        reaction type, and they are not merely isomer variants of each other.

        Parameters
        ----------
        errors : bool
            If ``True``, call ``sys.exit(1)`` when duplicates are detected.
        """
        has_duplicates = False
        for i, rea1 in enumerate(self.reactions):
            for rea2 in self.reactions[i + 1 :]:
                if rea1 == rea2:
                    if rea1.tmin != rea2.tmin or rea1.tmax != rea2.tmax:
                        continue
                    if rea1.is_isomer_version(rea2):
                        continue
                    if rea1.rtype() != rea2.rtype():
                        continue
                    self.logger.warning(
                        f"Duplicate reaction found: [cyan]{rea1.get_verbatim()}[/]"
                    )
                    has_duplicates = True

        if has_duplicates and errors:
            self.logger.error("Duplicate reactions found")
            sys.exit(1)

    def __generate_reaction_matrices(self) -> None:
        """Build integer stoichiometry matrices: shape (n_reactions × n_species)."""
        self.reactant_matrix = np.zeros(
            (self.reactions.count, self.species.count), dtype=int
        )
        self.product_matrix = np.zeros(
            (self.reactions.count, self.species.count), dtype=int
        )

        for i, reaction in enumerate(self.reactions):
            for reactant in reaction.reactants:
                self.reactant_matrix[i, reactant.index] += 1

            for product in reaction.products:
                self.product_matrix[i, product.index] += 1

    def __standardize_symbols(self, expr: Basic, replace_nH: bool) -> Basic:
        """Replace convenience symbols (nh, ne, ntot, n_X, …) with nden[i] references.

        When replace_nH is False, H/He element sums become ``nh``/``nhe`` symbols
        instead of being expanded over all species.
        """
        if expr == Float(0.0):
            return expr

        nden = MatrixSymbol("nden", self.species.count, 1)
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

        # n_X suffix convention: Xp→X+, X0→X, Xm→X-
        n_suffixes = {"p": "+", "m": "-", "0": ""}

        for fs in expr.free_symbols:
            name = str(fs)
            low_name = name.lower()
            repl = None

            if low_name == "ntot":
                repl = sum(nden[Idx(i)] for i in range(self.species.count))

            elif low_name == "nh":
                repl = get_element_sum("H") if replace_nH else symbols("nh")

            elif low_name in simple_map:
                spec_name = simple_map[low_name]
                repl = nden[Idx(self.species[spec_name].index)]

            elif low_name.startswith("n_"):
                core = name[2:]

                if core in ["H", "He"]:
                    if replace_nH:
                        repl = get_element_sum(core)
                    else:
                        repl = symbols(f"n{core.lower()}")

                else:
                    if core == "e":
                        core = "e-"
                    elif core[-1] in n_suffixes:
                        core = core[:-1] + n_suffixes[core[-1]]

                    if core in self.species:
                        repl = nden[Idx(self.species[core].index)]

            if repl is not None:
                reps[fs] = repl

        return expr.xreplace(reps)

    def sfluxes(self) -> list[Expr]:
        """Return symbolic flux expressions for all reactions.

        The flux of reaction *i* is ``rate_i * nden[r1] * nden[r2] * ...``,
        where the product runs over all reactant species.

        Returns
        -------
        list[Expr]
            One SymPy expression per reaction, in reaction-index order.
        """
        return get_sfluxes(self.reactions, self.species)

    def sodes(self) -> list[Basic]:
        """Return symbolic ODE right-hand sides for all species.

        Each entry is the net rate of change of a species number density
        (cm⁻³ s⁻¹), formed by summing flux contributions over all reactions
        in which the species participates as a reactant or product.

        Returns
        -------
        list[Basic]
            One SymPy expression per species, in species-index order.
        """
        return get_sodes(self.reactions, self.species)

    def sradodes(self, order: int = 0) -> list[Expr]:
        """Return symbolic radiation moment ODE right-hand sides.

        Parameters
        ----------
        order : int, optional
            Radiation moment order (0 = number/energy density, 1 = flux),
            by default ``0``.

        Returns
        -------
        list[Expr]
            One SymPy expression per radiation band.
        """
        return get_sradodes(self.radiation, self.species, order)

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
        """Write a pre-tabulated rate coefficient table to an HDF5 file.

        Parameters
        ----------
        fname : str | Path
            Output file path.  The ``.hdf5`` extension is recommended.
        label : str | None, optional
            Dataset label stored inside the file.  Defaults to
            ``self.label``.
        T_min : float | None, optional
            Minimum temperature for the tabulation grid (K).
        T_max : float | None, optional
            Maximum temperature for the tabulation grid (K).
        nT : int, optional
            Number of temperature grid points, by default 64.
        err_tol : float, optional
            Maximum allowed relative error in rate interpolation, default
            0.01 (1 %).
        rate_min : float, optional
            Rates below this threshold are clamped to ``rate_min``,
            default ``1e-30``.
        rate_max : float, optional
            Rates above this threshold are clamped to ``rate_max``,
            default ``1e100``.
        fast_log : bool, optional
            Use a fast logarithm approximation, default ``False``.
        include_all : bool, optional
            Include all reactions, even those with temperature bounds,
            default ``False``.
        verbose : bool, optional
            Print per-reaction tabulation progress, default ``False``.
        """
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
        """Write a pre-tabulated rate coefficient table to a plain-text file.

        Parameters are identical to ``to_hdf5``, except the output format is
        a whitespace-separated text table.

        Parameters
        ----------
        fname : str | Path
            Output file path.  The ``.txt`` extension is recommended.
        label : str | None, optional
            Dataset label stored in the file header.
        T_min : float | None, optional
            Minimum temperature (K).
        T_max : float | None, optional
            Maximum temperature (K).
        nT : int, optional
            Number of temperature grid points, default 64.
        err_tol : float, optional
            Maximum allowed relative interpolation error, default 0.01.
        rate_min : float, optional
            Lower rate clamp, default ``1e-30``.
        rate_max : float, optional
            Upper rate clamp, default ``1e100``.
        fast_log : bool, optional
            Use fast logarithm approximation, default ``False``.
        include_all : bool, optional
            Include temperature-bounded reactions, default ``False``.
        verbose : bool, optional
            Print tabulation progress, default ``False``.
        """
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
        """Write a pre-tabulated rate coefficient table in the specified format.

        This is the general-purpose version of ``to_hdf5`` / ``to_txt``.

        Parameters
        ----------
        fname : str | Path
            Output file path.
        label : str | None, optional
            Dataset label.  Defaults to ``self.label``.
        T_min : float | None, optional
            Minimum temperature (K).
        T_max : float | None, optional
            Maximum temperature (K).
        nT : int, optional
            Number of temperature grid points, default 64.
        err_tol : float, optional
            Maximum allowed relative interpolation error, default 0.01.
        rate_min : float, optional
            Lower rate clamp, default ``1e-30``.
        rate_max : float, optional
            Upper rate clamp, default ``1e100``.
        fast_log : bool, optional
            Use fast logarithm approximation, default ``False``.
        format : str, optional
            Output format: ``"hdf5"``, ``"txt"``, or ``"auto"`` (inferred
            from the file extension), default ``"auto"``.
        include_all : bool, optional
            Include temperature-bounded reactions, default ``False``.
        verbose : bool, optional
            Print tabulation progress, default ``False``.
        """
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
