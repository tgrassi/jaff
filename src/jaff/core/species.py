"""Chemical species representation and typed collections for JAFF networks.

A *specie* is a single molecular or atomic entity present in a reaction
network.  Each ``Specie`` instance carries its chemical name, mass (CGS),
elemental composition (the ``exploded`` atom list), charge, and a canonical
serialized form used for identity comparisons.

The serialized form sorts atom tokens alphabetically and joins them with
``"/"``.  For example ``H2O+`` becomes ``"+/H/H/O"`` — so structural isomers
(e.g. HCO+ and HOC+) share the same serialized form.

The ``fidx`` attribute encodes the species name as a C/Fortran-compatible
identifier (``"idx_X"`` for most species; ``"idx_e"`` for electrons).
"""

from __future__ import annotations

import re
import sys
from functools import cached_property
from itertools import product
from typing import TYPE_CHECKING

from ..io import JaffLogger
from ..types import Catalogue, Vector
from ._typing import ElementProps
from .elements import Elements

if TYPE_CHECKING:
    import logging


class Specie:
    """A single chemical species in a JAFF reaction network.

    Attributes
    ----------
    name : str
        Species name as it appears in the network file (e.g. ``"H2O+"``,
        ``"e-"``).
    mass : float or None
        Total mass in grams (CGS), summed over constituent atoms.  ``None``
        before ``parse`` has been called.
    exploded : list[str]
        Sorted list of atomic symbols with repetition
        (e.g. ``["H", "H", "O"]`` for H2O).  Charge tokens (``"+"``, ``"-"``)
        are included so that the serialized form encodes charge.
    charge : int
        Net charge in units of elementary charge.  Trailing ``"+"`` or
        ``"-"`` characters at the end of *name* are counted; ``e-`` always
        has charge ``-1``.
    index : int
        Position of this species in the parent ``Species`` catalogue.
    fidx : str
        Flat index identifier, safe for use in generated C/Fortran/Python
        source.  ``"+"`` maps to ``"j"`` and ``"-"`` maps to ``"k"``, so
        H2O+ becomes ``"idx_h2oj"``.  Electrons are special-cased to
        ``"idx_e"``.
    serialized : str
        Canonical form built by sorting *exploded* and joining with ``"/"``.
        Isomers share the same serialized form (e.g. HCO+ and HOC+ both
        become ``"+/C/H/O"``).
    elements : Elements
        Lazy-loaded ``Elements`` collection for this single species.
    """

    _ATTRS: frozenset[str] = frozenset(
        {"name", "mass", "exploded", "charge", "index", "fidx", "serialized", "elements"}
    )
    _mass_dict: dict | None = None

    @classmethod
    def configure(cls, mass_dict: dict[str, ElementProps]) -> None:
        """Override the mass dictionary and propagate it to ``Elements``.

        Parameters
        ----------
        mass_dict : dict[str, ElementProps]
            Custom mass dictionary.
        """
        cls._mass_dict = mass_dict
        Elements.configure(mass_dict)

    @classmethod
    def __get_mass_dict(cls) -> dict[str, ElementProps]:
        """Return the mass dictionary, loading it on first access.

        Returns
        -------
        dict[str, ElementProps]
            Mapping from element symbol to its properties.
        """
        if cls._mass_dict is None:
            from ..common import load_mass_dict

            cls._mass_dict = load_mass_dict()

        return cls._mass_dict

    def __init__(self, name: str, index: int = 0):
        """Construct a ``Specie`` and immediately parse its composition.

        Parameters
        ----------
        name : str
            Chemical formula as used in the network file.  The electron must
            be given as ``"e-"``; common misspellings (``"E"``, ``"E-"``,
            ``"electron"``, etc.) raise a fatal error.
        index : int, optional
            Position in the parent ``Species`` catalogue, by default ``0``.

        Raises
        ------
        SystemExit
            If *name* is a known misspelling of the electron species (the
            correct form is ``"e-"``).
        """
        self.logger: logging.Logger = JaffLogger().get_logger()
        if name.lower() in ["e", "eletron", "electrons", "el", "els"] or name in [
            "E",
            "E-",
        ]:
            self.logger.error(f"Electrons found with name: {name}. Use e- instead")
            sys.exit(1)

        self.name: str = name
        self.mass: float | None = None
        self.exploded: list[str] = []
        self.charge: int = 0
        self.index: int = index
        self.__latex: str = ""
        self.fidx: str = self.get_fidx()
        self.serialized: str = ""

        self._parse(self.__get_mass_dict())
        self.serialize()

    def __repr__(self):
        """Return detailed string representation of this species.

        Returns
        -------
        str
            String of the form ``"SpecieObject(<name>)"``.
        """
        return f"SpecieObject({self.name!r})"

    def __str__(self):
        """Return the species chemical name.

        Returns
        -------
        str
            Chemical name as used in the network file.
        """
        return self.name

    def __eq__(self, other):
        """Check equality by comparing species names.

        Parameters
        ----------
        other : Specie
            Species to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not a ``Specie`` instance.
        """
        if not isinstance(other, Specie):
            raise TypeError(
                f"'==' not supported between instances of 'Specie' and '{other}'"
            )

        return self.name == other.name

    def __hash__(self):
        """Return hash based on the species name.

        Returns
        -------
        int
        """
        return hash(self.name)

    def __lt__(self, other):
        """Compare species lexicographically by name.

        Parameters
        ----------
        other : Specie
            Species to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not a ``Specie`` instance.
        """
        if not isinstance(other, Specie):
            raise TypeError(
                f"'<' not supported between instances of 'Specie' and '{other}'"
            )

        return self.name < other.name

    @cached_property
    def elements(self) -> Elements:
        """Lazy ``Elements`` collection derived from this species' atoms.

        Returns
        -------
        Elements
        """
        return Elements(self)

    def get_fidx(self) -> str:
        """Compute the flat index identifier string for generated code.

        Returns
        -------
        str
            ``"idx_e"`` for electrons; otherwise ``"idx_<name>"`` with
            ``"+"`` replaced by ``"j"`` and ``"-"`` replaced by ``"k"``.
        """
        return (
            "idx_e"
            if self.name == "e-"
            else f"idx_{self.name.replace('+', 'j').replace('-', 'k').strip().lower()}"
        )

    @property
    def is_special(self) -> bool:
        """Whether this is a special pseudo-species.

        Special pseudo-species (``_PHOTON``, ``_CR``, ``_GRAIN``, ``_DUMMY``,
        ...) are radiation/cosmic-ray/grain agents and markers; they carry the
        reaction's identity but do not participate in the mass-action kinetics
        or the integrated ODE state.  They are identified by a leading
        underscore — real species never start with ``_`` (underscore-suffixed
        grain/ice species such as ``H2O_DUST`` have the underscore mid-name).

        Returns
        -------
        bool
        """
        return self.name.startswith("_")

    @property
    def is_core(self) -> bool:
        """Whether this is a core (real) species, i.e. not :attr:`is_special`.

        Returns
        -------
        bool
        """
        return not self.is_special

    def serialize(self) -> str:
        """Build and store the canonical serialized form of this species.

        The serialized form is ``"/".join(sorted(self.exploded))``, which
        places isomers into the same equivalence class.

        Returns
        -------
        str
            The serialized string (also stored in ``self.serialized``).
        """
        self.serialized = "/".join(sorted(self.exploded))

        return self.serialized

    def latex(self, dollars: bool = False):
        """Return a LaTeX representation of this species.

        Parameters
        ----------
        dollars : bool, optional
            When ``True``, wrap the string in ``$...$`` math delimiters,
            by default ``False``.

        Returns
        -------
        str
            LaTeX string with subscript digits, superscript charges, and
            ``\\rm`` roman font for element names.  Suffixes ``_ORTHO``,
            ``_PARA``, ``_META`` become ``o``, ``p``, ``m`` prefixes;
            ``_DUST`` becomes an ``ice`` suffix; ``GRAIN`` becomes ``g``.
        """
        return f"${self.__latex}$" if dollars else self.__latex

    def _parse(self, mass_dict: dict) -> None:
        """Parse *name* into elemental composition, mass, and charge.

        This is called automatically during ``__init__``.  It uses a proxy
        substitution strategy to avoid ambiguous greedy matches when element
        symbols are substrings of each other (e.g. ``"C"`` inside ``"Ca"``):
        each element symbol is temporarily replaced by a unique 4-character
        proxy drawn from the alphabet ``{q, z, x, j}``, the formula is
        tokenized, then proxies are reversed back to real symbols.

        Parameters
        ----------
        mass_dict : dict
            Mapping from element symbol to property dict (must contain at
            least the key ``"mass"``).

        Notes
        -----
        Numeric stoichiometry coefficients immediately following an element
        token are expanded into repeated atom entries (e.g. ``H2`` → ``["H",
        "H"]``).  The special coefficient ``"x"`` is treated as 1 so that
        wildcard species names are tolerated.

        Charge is determined by counting trailing ``"+"`` and ``"-"``
        characters at the *end* of the name only, which avoids misreading
        embedded signs (e.g. the lone minus in ``"e-"`` which is
        special-cased separately).
        """
        # Sort atoms longest-first so that multi-character symbols (e.g. "He")
        # are matched before single-character ones (e.g. "H").
        atoms = sorted(mass_dict.keys(), key=lambda x: len(x), reverse=True)
        ps = ["".join(x) for x in product("qzxj", repeat=4)][: len(atoms)]
        proxy = {a: p for a, p in zip(atoms, ps)}
        proxy_rev = {p: a for a, p in proxy.items()}

        pname = self.name.strip()
        for a in atoms:
            pname = pname.replace(a, f"${proxy[a]}$")

        def is_number(s: str) -> bool:
            if s == "x":
                return True
            try:
                float(s)
                return True
            except ValueError:
                return False

        alist = [x for x in pname.split("$") if x != ""]
        expl = []
        pold = None
        for p in alist:
            if not is_number(p):
                expl += [p]
            else:
                if p != "x":
                    # Repeat the previous atom (n-1) extra times to account
                    # for the first copy already appended in the previous step.
                    expl += [pold] * max(int(p) - 1, 1)
            pold = p
        self.exploded = sorted([proxy_rev[x] for x in expl])
        self.mass = sum([mass_dict[x]["mass"] for x in self.exploded])

        # --- Build LaTeX representation ---
        latex = self.name.strip()
        for i in range(0, 10):
            latex = latex.replace(str(i), "_{" + str(i) + "}")
        latex = re.sub(
            r"\++",
            lambda m: f"^{{{len(m.group()) if len(m.group()) > 1 else ''}+}}",
            latex,
        )
        latex = re.sub(
            r"-+",
            lambda m: f"^{{{len(m.group()) if len(m.group()) > 1 else ''}-}}",
            latex,
        )
        if "_ORTHO" in latex:
            latex = "o" + latex.replace("_ORTHO", "")
        if "_PARA" in latex:
            latex = "p" + latex.replace("_PARA", "")
        if "_META" in latex:
            latex = "m" + latex.replace("_META", "")
        if "_DUST" in latex:
            latex = latex.replace("_DUST", "") + "ice"

        latex = latex.replace("_GRAIN", "g")

        self.__latex = f"{{\\rm {latex}}}"

        # --- Determine net charge ---
        if self.name == "e-":
            self.charge = -1
            return

        self.charge = 0
        name = self.name
        # Count charge only at the end of the name so that mid-name hyphens
        # (e.g. compound names) are not misidentified as negative charges.
        while name.endswith("+") or name.endswith("-"):
            if name.endswith("+"):
                self.charge += 1
            elif name.endswith("-"):
                self.charge -= 1
            name = name[:-1]
        # self.charge = self.name.count("+") - self.name.count("-")


class Species(Catalogue[Specie]):
    """Ordered, name-indexed collection of ``Specie`` objects.

    Species supports look-up by name (``species["H2O"]``), by serialized form
    (``species["+/H/H/O"]``), and by integer index (``species[0]``).  The
    ``ne`` parameter on many accessor methods excludes the electron species
    (``"e-"``), which is often treated separately in network solvers.
    """

    _mass_dict: dict | None = None

    @classmethod
    def configure(cls, mass_dict: dict[str, ElementProps]) -> None:
        """Override the mass dictionary and propagate it to ``Specie``.

        Parameters
        ----------
        mass_dict : dict[str, ElementProps]
            Custom mass dictionary.
        """
        cls._mass_dict = mass_dict
        Specie.configure(mass_dict)

    def __init__(
        self,
        species: list[Specie] | list[str] | None = None,
        check_length: bool = True,
    ):
        """Initialise the species catalogue.

        Parameters
        ----------
        species : list[Specie] | list[str] | None, optional
            Initial species.  Plain strings are converted to ``Specie``
            objects with indices assigned in list order.  If ``None``, an
            empty catalogue is created (items can be added with ``add``).
        check_length : bool, optional
            If ``True`` (default), the base ``Catalogue`` verifies that the
            list and name-dict have the same length.  Set to ``False`` when
            constructing a catalogue from reactants/products that may contain
            duplicate species.
        """
        _by_name: dict[str, Specie] | None = None
        _by_serialized: dict[str, Specie] = {}

        if species is not None:
            if species and isinstance(species[0], str):
                species = [Specie(name, idx) for idx, name in enumerate(species)]  # type: ignore[arg-type]
            _by_name = {sp.name: sp for sp in species}  # type: ignore
            _by_serialized = {sp.serialized: sp for sp in species}  # type: ignore

        _species: list[Specie] = species  # type: ignore

        super().__init__(_species, _by_name, check_length)
        self._by_serialized = _by_serialized

    def __repr__(self):
        return f"Catalogue({self.names()!r})"

    def add(self, specie: Specie) -> None:
        """Append a new species to the catalogue if not already present.

        Duplicates (by name) are silently ignored.

        Parameters
        ----------
        specie : Specie
            The species to add.

        Raises
        ------
        ValueError
            If *specie* is not a ``Specie`` instance.
        """
        if not isinstance(specie, Specie):
            raise ValueError(f"'{specie}' must be an instance of 'Specie'")

        if specie.name not in self._by_name:
            self._by_name[specie.name] = specie
            self._by_serialized[specie.serialized] = specie
            self._list.append(specie)
            self.count = len(self._list)
            # Invalidate the cached core/special sub-catalogues on mutation.
            self.__dict__.pop("core", None)
            self.__dict__.pop("special", None)

    @cached_property
    def special(self) -> "Species":
        """Sub-catalogue of the special pseudo-species (``is_special``).

        Returns
        -------
        Species
        """
        return Species([s for s in self._list if s.is_special], check_length=False)

    @cached_property
    def core(self) -> "Species":
        """Sub-catalogue of the core (real) species (``is_core``).

        Used wherever only physically integrated species should participate —
        e.g. the mass-action density product and the ODE assembly — so the
        special pseudo-species are excluded from the kinetics.

        Returns
        -------
        Species
        """
        return Species([s for s in self._list if s.is_core], check_length=False)

    def from_serialized(self, serialized: str) -> Specie:
        """Return the species matching the given serialized form.

        Parameters
        ----------
        serialized : str
            Canonical serialized string (e.g. ``"+/H/H/O"``).

        Returns
        -------
        Specie
        """
        return self._by_serialized[serialized]

    def from_name(self, name: str) -> Specie:
        """Return the species with the given chemical name.

        Parameters
        ----------
        name : str
            Species name (e.g. ``"H2O+"``).

        Returns
        -------
        Specie
        """
        return self._by_name[name]

    def get_list(self) -> list[Specie]:
        """Return the underlying ordered list of ``Specie`` objects.

        Returns
        -------
        list[Specie]
        """
        return self._list

    def names(self, ne: bool = False) -> Vector[str]:
        """Return a ``Vector`` of species names.

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species (``"e-"``),
            by default ``False``.

        Returns
        -------
        Vector[str]
        """
        return Vector([s.name for s in self if not (ne and s.name == "e-")])

    def masses(self, ne: bool = False) -> Vector[float | None]:
        """Return a ``Vector`` of species masses in grams (CGS).

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[float | None]
        """
        return Vector([s.mass for s in self if not (ne and s.name == "e-")])

    def exploded(self, ne: bool = False) -> Vector[list[str]]:
        """Return a ``Vector`` of atom lists (one per species).

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[list[str]]
        """
        return Vector([s.exploded for s in self if not (ne and s.name == "e-")])

    def latex(self, dollars: bool = True, ne: bool = False) -> Vector[str]:
        """Return a ``Vector`` of LaTeX species strings.

        Parameters
        ----------
        dollars : bool, optional
            Wrap each string in ``$...$`` math delimiters, by default ``True``.
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[str]
        """
        return Vector([s.latex(dollars) for s in self if not (ne and s.name == "e-")])

    def charges(self, ne: bool = False) -> Vector[int]:
        """Return a ``Vector`` of net charges in units of elementary charge.

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[int]
        """
        return Vector([s.charge for s in self if not (ne and s.name == "e-")])

    def serialized(self, ne: bool = False) -> Vector[str]:
        """Return a ``Vector`` of canonical serialized species strings.

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[str]
        """
        return Vector([s.serialized for s in self if not (ne and s.name == "e-")])

    def elements(self, ne: bool = False) -> Vector[Elements]:
        """Return a ``Vector`` of ``Elements`` collections (one per species).

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[Elements]
        """
        return Vector([s.elements for s in self if not (ne and s.name == "e-")])

    def e_idx(self) -> int | None:
        """Return the integer index of the electron species, or ``None``.

        Returns
        -------
        int or None
            ``None`` when ``"e-"`` is not in this catalogue.
        """
        if "e-" in self:
            return self["e-"].index

    def normalized_names(self) -> Vector[str]:
        """Return species names normalized for use as code identifiers.

        All characters are lower-cased; ``"+"`` is replaced with ``"p"`` and
        ``"-"`` with ``"n"``.

        Returns
        -------
        Vector[str]
        """
        return Vector([s.name.lower().replace("+", "p").replace("-", "n") for s in self])

    def neutral(self, attr: str = "") -> Vector[Specie | int]:
        """Return neutral (charge == 0) species or one of their attributes.

        Parameters
        ----------
        attr : str, optional
            If given, return the named attribute of each neutral species
            instead of the ``Specie`` object itself.  Must be one of the
            values in ``Specie._ATTRS``.

        Returns
        -------
        Vector[Specie | int]

        Raises
        ------
        ValueError
            If *attr* is not a valid ``Specie`` attribute name.
        """
        if attr:
            if attr not in Specie._ATTRS:
                raise ValueError(f"Invalid attribute passed: {attr}")

            return Vector([getattr(s, attr) for s in self if s.charge == 0])

        return Vector([s for s in self if s.charge == 0])

    def charged(self, attr: str = "", ne: bool = False) -> Vector[Specie]:
        """Return charged (charge != 0) species or one of their attributes.

        Parameters
        ----------
        attr : str, optional
            If given, return the named attribute of each charged species.
            Must be one of the values in ``Specie._ATTRS``.
        ne : bool, optional
            If ``True``, exclude the electron species (``"e-"``),
            by default ``False``.

        Returns
        -------
        Vector[Specie]

        Raises
        ------
        ValueError
            If *attr* is not a valid ``Specie`` attribute name.
        """
        if attr:
            if attr not in Specie._ATTRS:
                raise ValueError(f"Invalid attribute passed: {attr}")

            return Vector(
                [
                    getattr(s, attr)
                    for s in self
                    if s.charge != 0 and not (ne and s.name == "e-")
                ]
            )

        return Vector([s for s in self if s.charge != 0 and not (ne and s.name == "e-")])

    def charge_truths(self, ne: bool = False) -> Vector[int]:
        """Return a binary ``Vector`` indicating whether each species is charged.

        Parameters
        ----------
        ne : bool, optional
            If ``True``, exclude the electron species, by default ``False``.

        Returns
        -------
        Vector[int]
            ``1`` for charged species, ``0`` for neutral.
        """
        return Vector([int(bool(s.charge)) for s in self if not (ne and s.name == "e-")])
