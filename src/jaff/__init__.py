"""JAFF - Just Another Fancy Format

Astrochemical reaction network parser supporting KROME, PRIZMO, UDFA, KIDA, and UCLChem formats.
"""

__version__ = "0.1.0"

from .core.elements import Element, Elements
from .core.network import Network
from .core._typing import NetworkProps
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
