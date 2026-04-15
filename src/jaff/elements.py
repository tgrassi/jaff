"""
Element extraction and matrix generation for chemical reaction networks.

This module provides utilities for extracting unique chemical elements from species
in a reaction network and generating element-related matrices for conservation laws
and stoichiometric analysis.
"""

from jaff import Network


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

    def __init__(self, network: Network) -> None:
        """
        Initialize the Elements analyzer for a given reaction network.

        Args:
            network: Chemical reaction network containing species to analyze.
        """
        self.net: Network = network
        self.elements: list[str] = []
        self.nelms = 0
        self.__set_elements()

    def __set_elements(self):
        """
        Extract unique chemical elements from all species in the network.

        Returns:
            List of unique element symbols (alphabetic characters only).
        """
        elements: set[str] = set()
        # Collect all elements from each species' exploded representation
        for specie in self.net.species:
            # Union with the set of atoms in this species
            elements |= set(specie.exploded)  # type: ignore[arg-type]

        # Filter to only alphabetic characters (element symbols) and convert to list
        self.elements = sorted(
            list({element for element in elements if element.isalpha()})
        )
        self.nelems = len(self.elements)

    def get_element_truth_matrix(self) -> list[list[int]]:
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
            [0] * len(self.net.species) for _ in range(self.nelems)
        ]

        # Populate matrix: 1 if element is in species, 0 otherwise
        for i, element in enumerate(self.elements):
            for j, specie in enumerate(self.net.species):
                element_truth_matrix[i][j] = int(element in specie.exploded)

        return element_truth_matrix

    def get_element_density_matrix(self) -> list[list[int]]:
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
            [0] * len(self.net.species) for _ in range(self.nelems)
        ]

        # Populate matrix with element counts for each species
        for i, element in enumerate(self.elements):
            for j, specie in enumerate(self.net.species):
                # Count occurrences of this element in this species
                element_density_matrix[i][j] = specie.exploded.count(element)

        return element_density_matrix
