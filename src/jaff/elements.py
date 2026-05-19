"""
Element extraction and matrix generation for chemical reaction networks.

This module provides utilities for extracting unique chemical elements from species
in a reaction network and generating element-related matrices for conservation laws
and stoichiometric analysis.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .types import Catalogue, Vector

if TYPE_CHECKING:
    from . import Specie
    from .common.helper import ElementProps


class Element:
    _register: dict = {}

    def __new__(cls, symbol: str, mass_dict: dict[str, ElementProps]):
        if symbol in cls._register:
            return cls._register[symbol]

        instance = super().__new__(cls)
        cls._register[symbol] = instance

        return instance

    def __init__(self, symbol: str, mass_dict: dict[str, ElementProps]):
        if getattr(self, "__initialized", False):
            return

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
        return f"Element(symbol={self.symbol!r}, name={self.name!r}"

    def __str__(self) -> str:
        return self.symbol

    def __eq__(self, other) -> bool:
        if not isinstance(other, Element):
            raise TypeError(
                f"'==' not supported between instances of 'Element' and '{other}'"
            )

        return self.symbol == other.symbol

    def __lt__(self, other) -> bool:
        if not isinstance(other, Element):
            raise TypeError(
                f"'<' not supported between instances of 'Element' and '{other}'"
            )

        return self.symbol < other.symbol

    def __hash__(self):
        return hash(self.symbol)


class Elements(Catalogue):
    """
    Extracts and manages chemical elements from a reaction network.

    This class analyzes all species in a chemical reaction network to extract
    unique chemical elements and provides methods to generate matrices that
    describe element composition and presence across all species.

    Attributes:
        net: The chemical reaction network to analyze.
        elements: Sorted list of unique chemical element symbols found in the network.
        count: Total number of unique elements in the network.
    """

    _register: dict = {}

    def __new__(cls, species: Specie | list[Specie], mass_dict: dict[str, ElementProps]):
        _species: list[Specie] = (
            list[species] if not isinstance(species, list) else species
        )  # type: ignore
        _serialized: str = "_".join(sorted(str(s) for s in _species))
        if _serialized in cls._register:
            return cls._register[_serialized]

        instance = super().__new__(cls)
        cls._register[_serialized] = instance

        return instance

    def __init__(
        self, species: Specie | list[Specie], mass_dict: dict[str, ElementProps]
    ) -> None:
        """
        Initialize the Elements analyzer for a given reaction network.

        Args:
            network: Chemical reaction network containing species to analyze.
        """
        if getattr(self, "__initialized", False):
            return

        self._mass_dict = mass_dict
        self.species: list[Specie] = species if isinstance(species, list) else [species]  # type: ignore

        self.__set_elements()
        self.__initalized = True

    def __set_elements(self) -> None:
        """
        Extract unique chemical elements from all species in the network.

        Returns:
            List of unique element symbols (alphabetic characters only).
        """
        elements: set[str] = set()

        # Collect all elements from each species' exploded representation
        for specie in self.species:
            # Union with the set of atoms in this species
            elements |= set(specie.exploded)  # type: ignore[arg-type]

        # Filter to only alphabetic characters (element symbols) and convert to list
        _list = sorted(
            list({Element(e, self._mass_dict) for e in elements if e.isalpha()})
        )

        _by_name = {e.name: e for e in _list}
        _by_symbol = {e.symbol: e for e in _list}

        super().__init__(_list, _by_symbol)
        self._by_serialized = _by_name

    @cache
    def truth_matrix(self) -> list[list[int]]:
        """
        Generate a binary matrix indicating element presence in each species.

        Creates a matrix where entry [i][j] is 1 if element i is present in
        species j, and 0 otherwise.

        Returns:
            2D matrix (count × nspecies) with binary values:
            - 1 if the element is present in the species
            - 0 if the element is absent from the species

        Example:
            For elements ['C', 'H', 'O'] and species ['CO', 'H2O', 'CH4']:
            [[1, 0, 1],   # C present in CO and CH4
             [0, 1, 1],   # H present in H2O and CH4
             [1, 1, 0]]   # O present in CO and H2O
        """
        # Initialize matrix with zeros (count rows × nspecies columns)
        element_truth_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.count)
        ]

        # Populate matrix: 1 if element is in species, 0 otherwise
        for i, element in enumerate(self._list):
            for j, specie in enumerate(self.species):
                element_truth_matrix[i][j] = int(element in specie.exploded)

        return element_truth_matrix

    @cache
    def density_matrix(self) -> list[list[int]]:
        """
        Generate a matrix showing element counts in each species.

        Creates a matrix where entry [i][j] represents the number of atoms of
        element i present in species j.

        Returns:
            2D matrix (count × nspecies) with integer counts representing
            the number of atoms of each element in each species.

        Example:
            For elements ['C', 'H', 'O'] and species ['CO', 'H2O', 'CH4']:
            [[1, 0, 1],   # C: 1 in CO, 0 in H2O, 1 in CH4
             [0, 2, 4],   # H: 0 in CO, 2 in H2O, 4 in CH4
             [1, 1, 0]]   # O: 1 in CO, 1 in H2O, 0 in CH4
        """
        # Initialize matrix with zeros (count rows × nspecies columns)
        element_density_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.count)
        ]

        # Populate matrix with element counts for each species
        for i, element in enumerate(self._list):
            for j, specie in enumerate(self.species):
                # Count occurrences of this element in this species
                element_density_matrix[i][j] = specie.exploded.count(element.symbol)

        return element_density_matrix

    def from_name(self, name: str) -> Element:
        return self._by_serialized[name]

    def from_symbol(self, symbol: str) -> Element:
        return self._by_name[symbol]

    def get_list(self) -> list[Element]:
        return self._list

    def symbols(self) -> Vector[str]:
        return Vector([e.symbol for e in self])

    def names(self) -> Vector[str]:
        return Vector([e.name for e in self])

    def masses(self) -> Vector[float]:
        return Vector([e.mass for e in self])

    def atomic_masses(self) -> Vector[float]:
        return Vector([e.atomic_mass for e in self])

    def protons(self) -> Vector[int]:
        return Vector([e.protons for e in self])

    def neutrons(self) -> Vector[int]:
        return Vector([e.neutrons for e in self])

    def electrons(self) -> Vector[int]:
        return Vector([e.electrons for e in self])
