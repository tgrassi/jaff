"""Reaction and Reactions classes for JAFF chemical networks.

A ``Reaction`` holds the symbolic rate expression, reactants, products, and
optional temperature bounds for a single astrochemical reaction.  The
companion ``Reactions`` catalogue indexes them by verbatim string and by
serialized form.

Serialized form
---------------
The serialized form of a reaction is::

    "<sorted_reactant_names>__<sorted_product_names>"

where species names are sorted alphabetically and joined with ``"_"``.
For example ``H + H2O+ -> H2O + H+`` serializes as
``"H_H2O+__H+_H2O"``.  This canonical form is used for equality testing,
hashing, and duplicate detection.

Reaction types
--------------
``rtype()`` classifies reactions by inspecting the symbolic rate expression:

- ``"photo"``       — rate contains a ``photorates(...)`` function call
- ``"cosmic_ray"``  — rate contains the symbol ``crate``
- ``"photo_av"``    — rate contains the symbol ``av``
- ``"3_body"``      — rate contains the symbol ``ntot``
- ``"unknown"``     — none of the above
"""

from __future__ import annotations

import sys
from functools import cached_property
from typing import TYPE_CHECKING, Any

import numpy as np
from sympy import (
    Basic,
    Function,
    ccode,
    cxxcode,
    fcode,
    julia_code,
    lambdify,
    pycode,
    rcode,
    rust_code,
    symbols,
    sympify,
)

from ..io import JaffLogger
from ..physics.photo_reactions._typing import XsecsProps
from ..types import Catalogue, Vector
from .elements import Elements
from .species import Specie, Species

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


class Reaction:
    """A single astrochemical reaction with a symbolic rate expression.

    Attributes
    ----------
    reactants : Species
        Ordered species catalogue of reactant species.
    products : Species
        Ordered species catalogue of product species.
    rate : Basic
        SymPy expression for the reaction rate coefficient (units depend on
        the reaction order; typically cm³ s⁻¹ for two-body reactions).
    tmin : float or None
        Minimum gas temperature at which the rate is valid (Kelvin).
        ``None`` means no lower bound.
    tmax : float or None
        Maximum gas temperature at which the rate is valid (Kelvin).
        ``None`` means no upper bound.
    dE : Basic
        SymPy expression for the energy released per reaction event (erg).
    dRad: Basic
        SymPy expression for the radiation energy emission per photon
        energy (eV) per reaction
    verbatim : str
        Human-readable string ``"R1 + R2 -> P1 + P2"``.
    index : int
        Position of this reaction in the parent ``Reactions`` catalogue.
    serialized : str
        Canonical form ``"<sorted_reactants>__<sorted_products>"``.
    serialized_exploded : str
        Like ``serialized`` but built from the atom-level serialized forms of
        each species (isomer-insensitive comparison).
    metadata : dict
        Arbitrary key/value store; ``metadata["type"]`` is populated by
        ``rtype()``.
    custom_rad_rate : bool
        ``True`` when the radiation rate was supplied via a ``.jfunc`` aux
        function rather than computed from cross-sections.
    xsecs_dict : dict or None
        Photo cross-section data for the reaction's single decay channel:
        ``photon_energy`` (eV), optional ``photo_absorption`` and the
        ``photodecay`` array (cm²), plus ``_equations`` metadata.  ``None`` for
        non-photo reactions.
    """

    def __init__(
        self,
        reactants: list[Specie],
        products: list[Specie],
        rate: Basic,
        tmin: float | None,
        tmax: float | None,
        dE: Basic,
        dRad: Basic,
        original_string: str,
        index: int,
        errors: bool = False,
    ):
        """Construct a ``Reaction`` and validate mass/charge conservation.

        Parameters
        ----------
        reactants : list[Specie]
            Reactant species (may contain duplicates for three-body reactions).
        products : list[Specie]
            Product species (may contain duplicates).
        rate : Basic
            SymPy expression for the rate coefficient.
        tmin : float or None
            Lower temperature bound in Kelvin, or ``None``.
        tmax : float or None
            Upper temperature bound in Kelvin, or ``None``.
        dE : Basic
            Energy change per event (erg), as a SymPy expression.
        dRad : Basic
            Radiation energy emission per photon energy, as a SymPy expression.
        original_string : str
            The raw network-file line that produced this reaction.
        index : int
            Zero-based position in the parent ``Reactions`` catalogue.
        errors : bool, optional
            If ``True``, terminate the process on mass or charge conservation
            violations instead of merely logging a warning, by default
            ``False``.

        Raises
        ------
        SystemExit
            When *errors* is ``True`` and mass or charge is not conserved.
        """
        self.logger = JaffLogger().get_logger()
        self.reactants: Species = Species(reactants, check_length=False)
        self.products: Species = Species(products, check_length=False)
        self.rate: Basic = rate
        self.tmin: float | None = tmin
        self.tmax: float | None = tmax
        self.dE: Basic = dE
        self.dRad: Basic = dRad
        self.custom_rad_rate: bool = False
        self.rad_xsecs: float | None = None
        self.xsecs_dict: XsecsProps | None = None
        self.original_string = original_string
        # verbatim is kept for backward compatibility alongside original_string
        self.verbatim: str = self.get_verbatim()
        self.index: int = index

        self.check(errors)
        self.serialized_exploded: str = self.serialize_exploded()
        self.serialized: str = self.serialize()
        self.metadata: dict = {}

        # Eagerly classify the reaction so metadata["type"] is populated.
        self.rtype()

    def __repr__(self):
        """Return detailed string representation of this reaction.

        Returns
        -------
        str
            String of the form ``"ReactionObject(<verbatim>)"``.
        """
        return f"ReactionObject({self.verbatim})"

    def __str__(self):
        """Return the human-readable verbatim reaction string.

        Returns
        -------
        str
            Verbatim form ``"R1 + R2 -> P1 + P2"``.
        """
        return self.verbatim

    def __eq__(self, other):
        """Check equality by comparing serialized (name-level) forms.

        Parameters
        ----------
        other : Reaction
            Reaction to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not a ``Reaction`` instance.
        """
        if not isinstance(other, Reaction):
            raise TypeError(
                f"'==' not supported between instances of 'Reaction' and '{other}'"
            )

        return self.serialized == other.serialized

    def __hash__(self):
        """Return hash based on the serialized (name-level) form.

        Returns
        -------
        int
        """
        return hash(self.serialized)

    def __lt__(self, other):
        """Compare reactions lexicographically by serialized form.

        Parameters
        ----------
        other : Reaction
            Reaction to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not a ``Reaction`` instance.
        """
        if not isinstance(other, Reaction):
            raise TypeError(
                f"'<' not supported between instances of 'Reaction' and '{other}'"
            )

        return self.serialized < other.serialized

    @cached_property
    def species(self) -> Species:
        """All unique species involved in this reaction (reactants ∪ products).

        Returns
        -------
        Species
        """
        return Species(list(set(self.reactants._list) | set(self.products._list)))

    @cached_property
    def elements(self) -> Elements:
        """All elements present across reactants and products.

        Returns
        -------
        Elements
        """
        return Elements(self.reactants._list + self.products._list)

    def rtype(self) -> str:
        """Classify this reaction by inspecting its rate expression.

        Returns
        -------
        str
            One of ``"photo"``, ``"cosmic_ray"``, ``"photo_av"``,
            ``"3_body"``, or ``"unknown"``.

        Notes
        -----
        Classification rules (evaluated in order):

        - ``"photo"``       — rate is or contains ``photorates(...)``
        - ``"cosmic_ray"``  — rate contains the free symbol ``crate``
        - ``"photo_av"``    — rate contains the free symbol ``av``
        - ``"3_body"``      — rate contains the free symbol ``ntot``
        - ``"unknown"``     — none of the above match

        The result is also cached in ``self.metadata["type"]``.
        """
        rtype = "unknown"

        if type(self.rate) is str:
            if "photo" in self.rate:
                rtype = "photo"
        else:
            if hasattr(self.rate, "func") and isinstance(
                self.rate.func, type(Function("f"))
            ):
                if self.rate.func.__name__ == "photorates":
                    rtype = "photo"
            elif self.rate.has(symbols("crate")):
                rtype = "cosmic_ray"
            elif self.rate.has(symbols("av")):
                rtype = "photo_av"
            elif self.rate.has(symbols("ntot")):
                rtype = "3_body"

        self.metadata["type"] = rtype

        return rtype

    def is_isomer_version(self, other: "Reaction") -> bool:
        """Check whether *other* is an isomer variant of this reaction.

        Two reactions are considered isomer versions of each other when they
        involve the same set of atoms on each side (same ``serialized_exploded``
        form) but differ in at least one species name.

        Parameters
        ----------
        other : Reaction
            The reaction to compare against.

        Returns
        -------
        bool
        """
        # Atom-level comparison ignores isomer distinctions (e.g. HCO+ ≡ HOC+).
        is_same_serialized = self.serialized_exploded == other.serialized_exploded

        # Name-level comparison detects the isomer distinction.
        rp1 = sorted([x.name for x in self.reactants._list + self.products._list])
        rp2 = sorted([x.name for x in other.reactants._list + other.products._list])
        has_different_species_names = rp1 != rp2

        return is_same_serialized and has_different_species_names

    def serialize_exploded(self) -> str:
        """Build the atom-level serialized form (isomer-insensitive).

        Each species is replaced by its ``Specie.serialized`` form (e.g.
        H2O+ → ``"+/H/H/O"``), then species tokens are sorted and joined
        with ``"_"``.  Reactants and products are separated by ``"__"``.

        Returns
        -------
        str
        """
        sr = "_".join(sorted([x.serialized for x in self.reactants]))
        sp = "_".join(sorted([x.serialized for x in self.products]))

        return f"{sr}__{sp}"

    def serialize(self) -> str:
        """Build the name-level serialized form (isomer-sensitive).

        Species names are sorted alphabetically and joined with ``"_"``.
        Reactants and products are separated by ``"__"``.

        Returns
        -------
        str
        """
        sr = "_".join(sorted([x.name for x in self.reactants]))
        sp = "_".join(sorted([x.name for x in self.products]))

        return f"{sr}__{sp}"

    def check(self, errors: bool) -> None:
        """Validate mass and charge conservation for this reaction.

        Parameters
        ----------
        errors : bool
            When ``True``, terminate the process on any conservation failure;
            when ``False``, only emit a warning.
        """
        if not self.check_mass():
            self.logger.warning(f"Mass not conserved in: {self.verbatim}")
            if errors:
                sys.exit(1)

        if not self.check_charge():
            self.logger.warning(f"Charge not conserved in: {self.verbatim}")
            if errors:
                sys.exit(1)

    def check_mass(self) -> bool:
        """Return ``True`` if mass is conserved within one electron mass.

        The tolerance (9.109e-28 g) is chosen to accommodate reactions that
        appear to gain or lose a single electron mass due to ionisation (the
        electron mass is negligible for chemistry purposes).

        Returns
        -------
        bool
        """
        return (
            abs(
                np.sum([r.mass for r in self.reactants])
                - np.sum([p.mass for p in self.products])
            )
            < 9.1093837e-28
        )

    def check_charge(self) -> bool:
        """Return ``True`` if the net charge is conserved.

        Returns
        -------
        bool
        """
        return (
            np.sum([x.charge for x in self.reactants])
            - np.sum([x.charge for x in self.products])
        ) == 0

    def get_verbatim(self) -> str:
        """Return a human-readable reaction string ``"R1 + R2 -> P1 + P2"``.

        Returns
        -------
        str
        """
        return (
            f"{' + '.join([x.name for x in self.reactants])}"
            " -> "
            f"{' + '.join([x.name for x in self.products])}"
        )

    def get_latex(self) -> str:
        """Return a LaTeX-formatted reaction equation wrapped in ``$...$``.

        Returns
        -------
        str
        """
        latex = (
            f"{' + '.join([r.latex() for r in self.reactants])}"
            "\\,\\to\\,"
            f"{' + '.join([x.latex() for x in self.products])}"
        )
        return f"${latex}$"

    def get_flux_expression(
        self,
        idx: int = 0,
        rate_variable: str = "k",
        species_variable: str = "y",
        brackets: str = "[]",
        idx_prefix: str = "",
    ) -> str:
        """Return a source-code string for the reaction flux.

        The flux has the form ``k[idx] * y[idx_R1] * y[idx_R2] * ...``,
        where ``idx_Ri`` is derived from each reactant's ``fidx`` attribute.

        Parameters
        ----------
        idx : int, optional
            Index into the rate-coefficient array, by default ``0``.
        rate_variable : str, optional
            Name of the rate array variable, by default ``"k"``.
        species_variable : str, optional
            Name of the species density array variable, by default ``"y"``.
        brackets : str, optional
            Two-character string whose first character is the left bracket and
            second is the right bracket (e.g. ``"[]"`` or ``"()"``),
            by default ``"[]"``.
        idx_prefix : str, optional
            Optional prefix prepended to each species index token, by default
            ``""``.

        Returns
        -------
        str

        Raises
        ------
        SystemExit
            If *brackets* is not exactly 2 characters.
        """
        if len(brackets) != 2:
            self.logger.error("Brackets must be a string of length 2, e.g. '[]'")
            sys.exit(1)

        lb, rb = brackets[0], brackets[1]
        flux = f"{rate_variable}{lb}{idx}{rb} * " + " * ".join(
            [f"{species_variable}{lb}{idx_prefix + x.fidx}{rb}" for x in self.reactants]
        )

        return flux

    def has_any_species(self, species: list[Specie | str] | str | Specie) -> bool:
        """Return ``True`` if *any* of *species* appear in reactants or products.

        Parameters
        ----------
        species : list[Specie | str] | str | Specie
            One or more species to test.

        Returns
        -------
        bool
        """
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return any(
            [x.name in sp_list for x in self.reactants._list + self.products._list]
        )

    def has_reactant(self, species: list[Specie | str] | str | Specie) -> bool:
        """Return ``True`` if *all* of *species* appear in the reactants.

        Parameters
        ----------
        species : list[Specie | str] | str | Specie
            One or more species to test.

        Returns
        -------
        bool
        """
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return all([s in self.reactants for s in sp_list])

    def has_product(self, species: list[Specie | str] | str | Specie) -> bool:
        """Return ``True`` if *all* of *species* appear in the products.

        Parameters
        ----------
        species : list[Specie | str] | str | Specie
            One or more species to test.

        Returns
        -------
        bool
        """
        sp_list: list[str] = []
        if isinstance(species, Specie):
            sp_list.append(species.name)
        elif isinstance(species, str):
            sp_list.append(species)
        elif isinstance(species, list):
            sp_list = [sp.name if isinstance(sp, Specie) else sp for sp in species]

        return all([s in self.products for s in sp_list])

    def get_code(self, lang="cpp") -> str:
        """Generate source code for the reaction rate expression.

        For photo-reactions whose rate is a ``photorates(n, lo, hi)`` call,
        the first argument (the photo-reaction index) is emitted as the
        placeholder ``$IDX$``, which the code generator replaces at a later
        stage with the actual array index.

        Parameters
        ----------
        lang : str, optional
            Target programming language, by default ``"cpp"``.
            Supported values: ``"python"``, ``"c"``, ``"cxx"``,
            ``"fortran"``, ``"rust"``, ``"julia"``, ``"r"``.

        Returns
        -------
        str
            Source code string for the rate expression.

        Raises
        ------
        ValueError
            If *lang* is not one of the supported language keys.
        """
        fmap = {
            "python": pycode,
            "c": ccode,
            "cxx": cxxcode,
            "fortran": fcode,
            "rust": rust_code,
            "julia": julia_code,
            "r": rcode,
        }

        if not fmap.get(lang, ""):
            raise ValueError(
                f"{lang} is not supported. Supported languages are:\n\n{fmap.keys()}"
            )
        if (
            hasattr(self.rate, "func")
            and isinstance(self.rate.func, type(Function("f")))
            and self.rate.func.__name__ == "photorates"
        ):
            # $IDX$ placeholder is replaced by the actual index at codegen time
            return (
                f"photorates($IDX$, {', '.join(str(arg) for arg in self.rate.args[1:])})"
            )

        return fmap[lang](self.get_sympy(), strict=False)

    def get_sympy(self) -> Basic:
        """Return the rate as a canonical SymPy expression.

        Returns
        -------
        Basic
        """
        return sympify(self.rate)

    def plot_rate_coefficient(
        self,
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        title: str | None = None,
        grid: bool = True,
        show: bool = True,
        save: bool = False,
        filename: str = "",
    ) -> tuple[plt.Figure, plt.Axes]:
        """Plot the rate coefficient as a function of gas temperature.

        The styled :class:`jaff.plotting.Plotter` is used so the figure
        matches the publication house style.

        Parameters
        ----------
        fig, ax : matplotlib objects or None, optional
            Existing figure/axes to draw on.  Created if ``None``.
        title : str or None, optional
            Plot title.  Defaults to the LaTeX reaction equation.
        grid : bool, optional
            Draw a grid, by default ``True``.
        show : bool, optional
            Display the figure, by default ``True``.
        save : bool, optional
            Save to *filename* (format inferred from extension).
        filename : str, optional
            Output path.  Defaults to ``"<reaction>_rate.png"``.

        Returns
        -------
        tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]

        Notes
        -----
        The temperature axis spans [``tmin``, ``tmax``] on a log scale.
        When ``tmin`` or ``tmax`` is ``None``, defaults of 2.73 K and 1e6 K
        are used respectively.
        """
        from ..plotting import Plotter

        tmin = 2.73 if self.tmin is None else self.tmin
        tmax = 1e6 if self.tmax is None else self.tmax

        tgas = np.logspace(np.log10(tmin), np.log10(tmax), 100)
        r = lambdify("tgas", self.rate, "numpy")
        y = np.array([r(t) for t in tgas])

        return Plotter().plot(
            x=tgas,
            y=y,
            fig=fig,
            ax=ax,
            xlabel="Temperature (K)",
            ylabel=r"Rate coefficient $k$",
            xscale="log",
            yscale="log",
            title=title or self.get_latex(),
            grid=grid,
            show=show,
            save=save,
            filename=filename or f"{self}_rate.png",
        )

    def plot_xsecs(
        self,
        processes: str | list[str] | None = "all",
        layout: str = "overlay",
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        energy_unit: str = "eV",
        xsec_unit: str = "Mb",
        energy_log: bool = True,
        xsecs_log: bool = True,
        title: str | None = None,
        grid: bool = True,
        show: bool = True,
        save: bool = False,
        filename: str = "",
    ) -> tuple[plt.Figure, Any] | None:
        """Plot photo cross sections against photon energy or wavelength.

        Parameters
        ----------
        processes : str | list[str] | None, optional
            Which cross-section processes to draw.  ``"all"`` (default) or
            ``None`` plots every process with data; a single key (e.g.
            ``"photodecay"``) or a list of keys selects a subset.
            Valid keys: ``"photo_absorption"``, ``"photodecay"``.
        layout : str, optional
            ``"overlay"`` (default) draws all processes on one axes;
            ``"subplots"`` gives each process its own stacked panel.
        ax : matplotlib.axes.Axes or None, optional
            Axes to draw on (overlay only).  If ``None``, a figure is created.
        energy_unit : str, optional
            Horizontal-axis unit: ``"eV"`` (default), ``"erg"``, ``"nm"``,
            ``"um"``.
        xsec_unit : str, optional
            Cross-section unit for the vertical axis, by default ``"Mb"``
            (megabarn); ``"cm^2"`` and ``"barn"`` are also accepted.
        energy_log, xsecs_log : bool, optional
            Log-scale the energy / cross-section axis (default ``True``).

        Returns
        -------
        tuple[matplotlib.figure.Figure, matplotlib.axes.Axes] or None
            The figure and axes, or ``None`` when there is nothing to draw.

        Notes
        -----
        Does nothing (logs a message) if ``self.xsecs_dict`` is ``None`` or no
        requested process has data.  Drawing, unit conversion and labelling are
        delegated to :meth:`jaff.plotting.Plotter.plot_xsec`.
        """
        from ..plotting import Plotter

        if self.xsecs_dict is None:
            self.logger.info(f"No cross sections available for: {self}")
            return None

        _XSEC_PROCESSES = (
            "photo_absorption",
            "photodecay",
        )

        # Normalise the process selection to a list of valid keys.
        if processes is None or processes == "all":
            procs = list(_XSEC_PROCESSES)
        elif isinstance(processes, str):
            procs = [processes]
        else:
            procs = list(processes)

        invalid = [p for p in procs if p not in _XSEC_PROCESSES]
        if invalid:
            raise KeyError(
                f"Invalid cross-section(s) {invalid}. Supported: "
                f"{', '.join(_XSEC_PROCESSES)}"
            )

        # Keep only processes that actually carry data for this reaction.
        available = [p for p in procs if self.xsecs_dict.get(p) is not None]
        if not available:
            self.logger.info(f"No data for requested cross-section(s) {procs} in: {self}")
            return

        if not filename:
            stem = available[0] if len(available) == 1 else "cross_sections"
            filename = f"{self}_{stem}.png"

        return Plotter().plot_xsec(
            self.xsecs_dict,
            processes=available,
            layout=layout,
            fig=fig,
            ax=ax,
            energy_unit=energy_unit,
            xsec_unit=xsec_unit,
            energy_log=energy_log,
            xsec_log=xsecs_log,
            title=title or self.get_latex(),
            grid=grid,
            show=show,
            save=save,
            filename=filename,
        )


class Reactions(Catalogue[Reaction]):
    """Ordered, doubly-indexed catalogue of ``Reaction`` objects.

    Reactions can be looked up by verbatim string (``reactions["H + H2O+ -> H2 + OH+"]``)
    or by serialized form (``reactions["H_H2O+__H2_OH+"]``).
    """

    def __init__(self, reactions: list[Reaction] | None = None):
        """Initialise the reactions catalogue.

        Parameters
        ----------
        reactions : list[Reaction] | None, optional
            Initial reactions.  If ``None``, an empty catalogue is created.
        """
        _by_name: dict[str, Reaction] | None = None
        _by_serialized: dict[str, Reaction] = {}

        if reactions is not None:
            _by_name = {r.verbatim: r for r in reactions}
            _by_serialized = {r.serialized: r for r in reactions}

        super().__init__(reactions, _by_name)
        self._by_serialized = _by_serialized

    def __repr__(self):
        return f"Catalogue({self.verbatim()!r})"

    def add(self, reaction: Reaction) -> None:
        """Append a reaction to the catalogue (duplicates are not checked here).

        Parameters
        ----------
        reaction : Reaction

        Raises
        ------
        ValueError
            If *reaction* is not a ``Reaction`` instance.
        """
        if not isinstance(reaction, Reaction):
            raise ValueError(f"'{reaction}' must be an instance of 'Reaction'")

        self._by_name[reaction.verbatim] = reaction
        self._by_serialized[reaction.serialized] = reaction
        self._list.append(reaction)
        self.count = len(self._list)

    def from_serialized(self, serialized: str) -> Reaction:
        """Look up a reaction by its serialized form.

        Parameters
        ----------
        serialized : str
            Canonical form ``"<sorted_reactants>__<sorted_products>"``.

        Returns
        -------
        Reaction
        """
        return self._by_serialized[serialized]

    def from_verbatim(self, verbatim: str, rtype: str | None = None) -> Reaction | None:
        """Look up a reaction by its verbatim string.

        Parameters
        ----------
        verbatim : str
            Human-readable string (e.g. ``"H + H2O+ -> H2 + OH+"``).
        rtype : str or None, optional
            If supplied, return ``None`` when the reaction type does not match.

        Returns
        -------
        Reaction or None
        """
        rea = self._by_name[verbatim]
        if rtype is None or rea.rtype() == rtype:
            return rea

    def get_list(self) -> list[Reaction]:
        """Return the underlying ordered list of ``Reaction`` objects.

        Returns
        -------
        list[Reaction]
        """
        return self._list

    def get(self, reaction: str, rtype: str | None = None) -> Reaction | None:
        """Look up a reaction by name or serialized form, with optional type filter.

        Parameters
        ----------
        reaction : str
            Verbatim string or serialized form.
        rtype : str or None, optional
            If given, return ``None`` when the reaction type does not match.

        Returns
        -------
        Reaction or None
        """
        rea = self[reaction]
        if rtype is None or rea.rtype() == rtype:
            return rea

    def with_rtype(self, rtype: str):
        """Return all reactions matching the given reaction type.

        Parameters
        ----------
        rtype : str
            One of ``"photo"``, ``"cosmic_ray"``, ``"photo_av"``,
            ``"3_body"``, ``"unknown"``.

        Returns
        -------
        Vector[Reaction]
        """
        return Vector([r for r in self if r.rtype() == rtype])

    def verbatim(self) -> Vector[str]:
        """Return a ``Vector`` of verbatim reaction strings.

        Returns
        -------
        Vector[str]
        """
        return Vector([r.verbatim for r in self])

    def rtypes(self) -> Vector[str]:
        """Return a ``Vector`` of reaction type strings.

        Returns
        -------
        Vector[str]
        """
        return Vector([r.rtype() for r in self])

    def reactants(self) -> Vector[Species]:
        """Return a ``Vector`` of reactant ``Species`` catalogues.

        Returns
        -------
        Vector[Species]
        """
        return Vector([r.reactants for r in self])

    def products(self) -> Vector[Species]:
        """Return a ``Vector`` of product ``Species`` catalogues.

        Returns
        -------
        Vector[Species]
        """
        return Vector([r.products for r in self])

    def rates(self) -> Vector[Basic]:
        """Return a ``Vector`` of rate SymPy expressions.

        Returns
        -------
        Vector[Basic]
        """
        return Vector([r.rate for r in self])

    def tmins(self) -> Vector[float | None]:
        """Return a ``Vector`` of lower temperature bounds (K or ``None``).

        Returns
        -------
        Vector[float | None]
        """
        return Vector([r.tmin for r in self])

    def tmaxes(self) -> Vector[float | None]:
        """Return a ``Vector`` of upper temperature bounds (K or ``None``).

        Returns
        -------
        Vector[float | None]
        """
        return Vector([r.tmax for r in self])

    def dE(self) -> Vector[Basic]:
        """Return a ``Vector`` of energy-change SymPy expressions (erg).

        Returns
        -------
        Vector[Basic]
        """
        return Vector([r.dE for r in self])

    def dRad(self) -> Vector[Basic]:
        """Return a ``Vector`` of radiation-rate SymPy expressions.

        Returns
        -------
        Vector[Basic]
        """
        return Vector([r.dRad for r in self])

    def serialized(self) -> Vector[str]:
        """Return a ``Vector`` of name-level serialized reaction strings.

        Returns
        -------
        Vector[str]
        """
        return Vector([r.serialized for r in self])

    def serialized_exploded(self) -> Vector[str]:
        """Return a ``Vector`` of atom-level (isomer-insensitive) serialized strings.

        Returns
        -------
        Vector[str]
        """
        return Vector([r.serialized_exploded for r in self])

    def photo_reactions(self) -> Vector[Reaction]:
        """Return all photo-reactions (``rtype == "photo"``).

        Returns
        -------
        Vector[Reaction]
        """
        return Vector([r for r in self if r.rtype() == "photo"])

    def photo_reaction_truths(self) -> Vector[int]:
        """Return a binary ``Vector`` marking photo-reactions with ``1``.

        Returns
        -------
        Vector[int]
        """
        return Vector([int(reaction.rtype() == "photo") for reaction in self])

    def photo_reaction_indices(self) -> Vector[int]:
        """Return the integer indices of photo-reactions within this catalogue.

        Returns
        -------
        Vector[int]
        """
        return Vector(
            [i for i, reaction in enumerate(self) if reaction.rtype() == "photo"]
        )
