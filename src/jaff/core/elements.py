"""Element extraction and composition matrices for chemical networks.

This module provides two classes:

- `Element`: a flyweight representing a single chemical element, loaded from
  the JAFF mass dictionary (CGS units throughout).
- `Elements`: an ordered, unique collection of elements derived from a list of
  `Specie` objects, with helpers for building truth and density matrices used
  in stoichiometry calculations.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from ..types import Catalogue, Vector

if TYPE_CHECKING:
    from . import Specie
    from ._typing import ElementProps


class Element:
    """A chemical element loaded from the JAFF mass dictionary.

    Instances are flyweights: constructing ``Element("H")`` twice returns the
    same object.  The first construction populates all attributes from the
    mass dictionary; subsequent constructions are no-ops.

    Attributes
    ----------
    symbol : str
        Periodic-table symbol (e.g. ``"H"``, ``"He"``).
    name : str
        Full element name (e.g. ``"hydrogen"``).
    mass : float
        Mass of the most common isotope in grams (CGS).
    atomic_mass : float
        Standard atomic weight in atomic mass units.
    protons : int
        Number of protons (atomic number).
    neutrons : int
        Number of neutrons in the most common isotope.
    electrons : int
        Number of electrons in the neutral atom.
    """

    _register: dict = {}
    _mass_dict: dict | None = None

    @classmethod
    def configure(cls, mass_dict: dict[str, ElementProps]) -> None:
        """Override the mass dictionary used to instantiate elements.

        Call this before creating any ``Element`` instances if you need a
        custom mass table.  Calling it after elements have already been
        registered has no effect on those existing instances.

        Parameters
        ----------
        mass_dict : dict[str, ElementProps]
            Mapping from element symbol to a dict with keys ``"name"``,
            ``"mass"``, ``"atomic_mass"``, ``"protons"``, ``"neutrons"``,
            ``"electrons"``.
        """
        cls._mass_dict = mass_dict

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

    def __new__(cls, symbol: str):
        """Return the flyweight instance for *symbol*, creating it if absent.

        Parameters
        ----------
        symbol : str
            Periodic-table symbol (case-sensitive).

        Returns
        -------
        Element
            Existing cached instance, or a newly allocated one registered for
            future calls.
        """
        # Return the cached instance if this element has already been built;
        # otherwise create a fresh one and register it for future look-ups.
        if symbol in cls._register:
            return cls._register[symbol]

        instance = super().__new__(cls)
        cls._register[symbol] = instance

        return instance

    def __init__(self, symbol: str):
        """Initialise an Element from the mass dictionary.

        Parameters
        ----------
        symbol : str
            Periodic-table symbol of the element (case-sensitive, e.g. ``"He"``).

        Raises
        ------
        KeyError
            If *symbol* is not present in the mass dictionary.
        """
        if getattr(self, "__initialized", False):
            return

        mass_dict = self.__get_mass_dict()

        if symbol not in mass_dict:
            raise KeyError(f"No specie found in mass dictionary: {symbol}")

        self.symbol: str = symbol
        self.name: str = mass_dict[symbol]["name"]
        self.mass: float = mass_dict[symbol]["mass"]
        self.atomic_mass: float = mass_dict[symbol]["atomic_mass"]
        self.protons: int = mass_dict[symbol]["protons"]
        self.neutrons: int = mass_dict[symbol]["neutrons"]
        self.electrons: int = mass_dict[symbol]["electrons"]
        self.__initialized = True

    def __repr__(self) -> str:
        """Return detailed string representation of this element.

        Returns
        -------
        str
            String including symbol and full element name.
        """
        return f"ElementObject(symbol={self.symbol!r})"

    def __str__(self) -> str:
        """Return the periodic-table symbol.

        Returns
        -------
        str
            Element symbol (e.g. ``"He"``).
        """
        return self.symbol

    def __eq__(self, other) -> bool:
        """Check equality by comparing element symbols.

        Parameters
        ----------
        other : Element
            Element to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not an ``Element`` instance.
        """
        if not isinstance(other, Element):
            raise TypeError(
                f"'==' not supported between instances of 'Element' and '{other}'"
            )

        return self.symbol == other.symbol

    def __lt__(self, other) -> bool:
        """Compare elements lexicographically by symbol.

        Parameters
        ----------
        other : Element
            Element to compare against.

        Returns
        -------
        bool

        Raises
        ------
        TypeError
            If *other* is not an ``Element`` instance.
        """
        if not isinstance(other, Element):
            raise TypeError(
                f"'<' not supported between instances of 'Element' and '{other}'"
            )

        return self.symbol < other.symbol

    def __hash__(self):
        """Return hash based on the element symbol.

        Returns
        -------
        int
        """
        return hash(self.symbol)


class Elements(Catalogue):
    """Sorted, deduplicated collection of elements derived from a species list.

    ``Elements`` is also a flyweight: instances with the same sorted species
    set are reused.  The internal order follows alphabetical sort on element
    symbol, which fixes the row order of the composition matrices.

    Attributes
    ----------
    species : list[Specie]
        The input species whose atoms were used to populate this collection.
    count : int
        Number of unique elements present (inherited from ``Catalogue``).
    """

    _register: dict = {}
    _mass_dict: dict | None = None

    @classmethod
    def configure(cls, mass_dict: dict[str, ElementProps]) -> None:
        """Override the mass dictionary for both ``Elements`` and ``Element``.

        Parameters
        ----------
        mass_dict : dict[str, ElementProps]
            Custom mass dictionary forwarded to ``Element.configure`` as well.
        """
        cls._mass_dict = mass_dict
        Element.configure(mass_dict)

    @classmethod
    def __get_mass_dict(cls) -> dict[str, ElementProps]:
        """Return the mass dictionary for the ``Elements`` collection.

        Returns
        -------
        dict[str, ElementProps]
            Mapping from element symbol to its properties.
        """
        if cls._mass_dict is None:
            from ..common import load_mass_dict

            cls._mass_dict = load_mass_dict()
        return cls._mass_dict

    @staticmethod
    def __get_species_list(
        species: Specie | list[Specie] | str | list[str],
    ) -> list[Specie]:
        """Normalise the *species* argument to a ``list[Specie]``."""
        from .species import Specie as _Specie

        if isinstance(species, str):
            return [_Specie(species, 0)]

        if isinstance(species, list) and species and isinstance(species[0], str):
            return [_Specie(name, idx) for idx, name in enumerate(species)]  # type: ignore[arg-type]

        if not isinstance(species, list):
            return [species]  # type: ignore[list-item]

        return species  # type: ignore

    def __new__(cls, species: Specie | list[Specie] | str | list[str]):
        """Return the flyweight ``Elements`` instance for the given species set.

        Parameters
        ----------
        species : Specie | list[Specie] | str | list[str]
            Species whose atoms define the element set.

        Returns
        -------
        Elements
            Existing cached instance keyed by the sorted species serialization,
            or a newly allocated one.
        """
        # Serialise the species set to a canonical key for flyweight look-up.
        _species = cls.__get_species_list(species)
        _serialized: str = "_".join(sorted(str(s) for s in _species))
        if _serialized in cls._register:
            return cls._register[_serialized]

        instance = super().__new__(cls)
        cls._register[_serialized] = instance

        return instance

    def __init__(self, species: Specie | list[Specie] | str | list[str]) -> None:
        """Build the element collection from *species*.

        Parameters
        ----------
        species : Specie | list[Specie] | str | list[str]
            One or more species whose constituent atoms define the element set.
            Plain strings are converted to ``Specie`` objects on the fly.
        """
        if getattr(self, "__initialized", False):
            return

        self.species: list[Specie] = self.__get_species_list(species)

        self.__set_elements()
        self.__initalized = True

    def __repr__(self):
        return f"Catalogue({self.symbols()!r})"

    def __set_elements(self) -> None:
        """Collect unique alphabetic atoms across all species and build indices."""
        elements: set[str] = set()

        for specie in self.species:
            elements |= set(specie.exploded)  # type: ignore[arg-type]

        # Filter out charge tokens ('+', '-') — only real element symbols remain.
        _list = sorted(list({Element(e) for e in elements if e.isalpha()}))

        _by_name = {e.name: e for e in _list}
        _by_symbol = {e.symbol: e for e in _list}

        super().__init__(_list, _by_symbol)
        # _by_serialized is reused here to store the name→Element mapping.
        self._by_serialized = _by_name

    @cache
    def truth_matrix(self) -> list[list[int]]:
        """Binary element-presence matrix.

        Returns
        -------
        list[list[int]]
            A 2-D integer matrix of shape ``(n_elements, n_species)``.
            Entry ``[i][j]`` is ``1`` if element *i* appears at least once in
            species *j*, otherwise ``0``.

        Notes
        -----
        The result is cached after the first call (via ``functools.cache``).
        Row order matches the sorted element list; column order matches the
        order of *species* passed to ``__init__``.
        """
        element_truth_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.count)
        ]

        for i, element in enumerate(self._list):
            for j, specie in enumerate(self.species):
                element_truth_matrix[i][j] = int(str(element) in specie.exploded)

        return element_truth_matrix

    @cache
    def density_matrix(self) -> list[list[int]]:
        """Atom-count matrix (stoichiometric composition matrix).

        Returns
        -------
        list[list[int]]
            A 2-D integer matrix of shape ``(n_elements, n_species)``.
            Entry ``[i][j]`` is the number of atoms of element *i* contained
            in species *j* (e.g. entry for H in H2O is ``2``).

        Notes
        -----
        The result is cached after the first call (via ``functools.cache``).
        """
        element_density_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.count)
        ]

        for i, element in enumerate(self._list):
            for j, specie in enumerate(self.species):
                element_density_matrix[i][j] = specie.exploded.count(element.symbol)

        return element_density_matrix

    def from_name(self, name: str) -> Element:
        """Return the ``Element`` with the given full name (e.g. ``"hydrogen"``).

        Parameters
        ----------
        name : str
            Full element name as stored in the mass dictionary.

        Returns
        -------
        Element
        """
        return self._by_serialized[name]

    def from_symbol(self, symbol: str) -> Element:
        """Return the ``Element`` with the given periodic-table symbol.

        Parameters
        ----------
        symbol : str
            Element symbol (e.g. ``"H"``).

        Returns
        -------
        Element
        """
        return self._by_name[symbol]

    def get_list(self) -> list[Element]:
        """Return the underlying ordered list of ``Element`` objects.

        Returns
        -------
        list[Element]
        """
        return self._list

    def symbols(self) -> Vector[str]:
        """Return a ``Vector`` of element symbols in sorted order.

        Returns
        -------
        Vector[str]
        """
        return Vector([e.symbol for e in self])

    def names(self) -> Vector[str]:
        """Return a ``Vector`` of full element names in sorted order.

        Returns
        -------
        Vector[str]
        """
        return Vector([e.name for e in self])

    def masses(self) -> Vector[float]:
        """Return a ``Vector`` of element masses in grams (CGS).

        Returns
        -------
        Vector[float]
        """
        return Vector([e.mass for e in self])

    def atomic_masses(self) -> Vector[float]:
        """Return a ``Vector`` of standard atomic weights in atomic mass units.

        Returns
        -------
        Vector[float]
        """
        return Vector([e.atomic_mass for e in self])

    def protons(self) -> Vector[int]:
        """Return a ``Vector`` of proton counts (atomic numbers).

        Returns
        -------
        Vector[int]
        """
        return Vector([e.protons for e in self])

    def neutrons(self) -> Vector[int]:
        """Return a ``Vector`` of neutron counts for the most common isotope.

        Returns
        -------
        Vector[int]
        """
        return Vector([e.neutrons for e in self])

    def electrons(self) -> Vector[int]:
        """Return a ``Vector`` of electron counts for the neutral atom.

        Returns
        -------
        Vector[int]
        """
        return Vector([e.electrons for e in self])
