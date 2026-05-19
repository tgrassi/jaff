"""
Element extraction and matrix generation for chemical reaction networks.

This module provides utilities for extracting unique chemical elements from species
in a reaction network and generating element-related matrices for conservation laws
and stoichiometric analysis.
"""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from . import Species

if TYPE_CHECKING:
    from .common.helper import ElementProps


class Element:
    _register: dict = {}

    def __new__(cls, symbol: str, mass_dict: dict[str, ElementProps]):
        if symbol in cls._register:
            return cls._register[symbol]

        instance = super().__init__(cls)
        cls._register[symbol] = instance

        return instance

    def __init__(self, symbol: str, mass_dict: dict[str, ElementProps]):
        if getattr(self, "_initialized", False):
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

    def __repr__(self) -> str:
        return f"Element(symbol={self.symbol!r}, name={self.name!r}"

    def __str__(self) -> str:
        return self.symbol


class Elements:
    """
    Extracts and manages chemical elements from a reaction network.

    This class analyzes all species in a chemical reaction network to extract
    unique chemical elements and provides methods to generate matrices that
    describe element composition and presence across all species.

    Attributes:
        net: The chemical reaction network to analyze.
        elements: Sorted list of unique chemical element symbols found in the network.
        nelems: Total number of unique elements in the network.
    """

    def __init__(
        self, species: Species | list[Species], mass_dict: dict[str, ElementProps]
    ) -> None:
        """
        Initialize the Elements analyzer for a given reaction network.

        Args:
            network: Chemical reaction network containing species to analyze.
        """
        self._mass_dict = mass_dict
        self.list: list[Element] = []
        self.index: dict[str, int] = {}
        self.species: list[Species] = (
            [species] if isinstance(species, Species) else species
        )

        self.nelms: int = 0

        self._set_elements()

    def _set_elements(self) -> None:
        """
        Extract unique chemical elements from all species in the network.

        Returns:
            List of unique element symbols (alphabetic characters only).
        """
        elements: set[str] = set()
        if isinstance(self.species, Species):
            species = [self.species]

        # Collect all elements from each species' exploded representation
        for specie in species:
            # Union with the set of atoms in this species
            elements |= set(specie.exploded)  # type: ignore[arg-type]

        # Filter to only alphabetic characters (element symbols) and convert to list
        self.list = sorted(
            list({Element(e, self._mass_dict) for e in elements if e.isalpha()})
        )
        for i, e in enumerate(self.list):
            self.index[e.name] = i
            self.index[e.symbol] = i

        self.nelems = len(self.list)

    @cache
    def truth_matrix(self) -> list[list[int]]:
        """
        Generate a binary matrix indicating element presence in each species.

        Creates a matrix where entry [i][j] is 1 if element i is present in
        species j, and 0 otherwise.

        Returns:
            2D matrix (nelems × nspecies) with binary values:
            - 1 if the element is present in the species
            - 0 if the element is absent from the species

        Example:
            For elements ['C', 'H', 'O'] and species ['CO', 'H2O', 'CH4']:
            [[1, 0, 1],   # C present in CO and CH4
             [0, 1, 1],   # H present in H2O and CH4
             [1, 1, 0]]   # O present in CO and H2O
        """
        # Initialize matrix with zeros (nelems rows × nspecies columns)
        element_truth_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.nelems)
        ]

        # Populate matrix: 1 if element is in species, 0 otherwise
        for i, element in enumerate(self.list):
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
            2D matrix (nelems × nspecies) with integer counts representing
            the number of atoms of each element in each species.

        Example:
            For elements ['C', 'H', 'O'] and species ['CO', 'H2O', 'CH4']:
            [[1, 0, 1],   # C: 1 in CO, 0 in H2O, 1 in CH4
             [0, 2, 4],   # H: 0 in CO, 2 in H2O, 4 in CH4
             [1, 1, 0]]   # O: 1 in CO, 1 in H2O, 0 in CH4
        """
        # Initialize matrix with zeros (nelems rows × nspecies columns)
        element_density_matrix: list[list[int]] = [
            [0] * len(self.species) for _ in range(self.nelems)
        ]

        # Populate matrix with element counts for each species
        for i, element in enumerate(self.list):
            for j, specie in enumerate(self.species):
                # Count occurrences of this element in this species
                element_density_matrix[i][j] = specie.exploded.count(element.symbol)

        return element_density_matrix
