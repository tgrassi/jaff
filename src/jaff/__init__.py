# ABOUTME: Entry point for the JAFF package
# ABOUTME: Exports main classes and functions for chemical network parsing

"""JAFF - Just Another Fancy Format

An astrochemical network parser for various reaction network formats.
"""

__version__ = "0.1.0"

from .core.elements import Element, Elements
from .core.network import Network, NetworkProps
from .core.reaction import Reaction, Reactions
from .core.species import Specie, Species
from .codegen.builder import Builder
from .codegen.codegen import Codegen
from .codegen.preprocessor import Preprocessor

__all__ = [
    "Element",
    "Elements",
    "Network",
    "NetworkProps",
    "Reaction",
    "Reactions",
    "Specie",
    "Species",
    "Builder",
    "Codegen",
    "Preprocessor",
]
