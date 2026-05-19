# ABOUTME: Entry point for the JAFF package
# ABOUTME: Exports main classes and functions for chemical network parsing

"""JAFF - Just Another Fancy Format

An astrochemical network parser for various reaction network formats.
"""

__version__ = "0.1.0"

from .builder import Builder
from .codegen import Codegen
from .network import Network
from .preprocessor import Preprocessor
from .reaction import Reaction, Reactions
from .species import Specie, Species

__all__ = [
    "Builder",
    "Network",
    "Reaction",
    "Reactions",
    "Specie",
    "Species",
    "Codegen",
    "Preprocessor",
]
