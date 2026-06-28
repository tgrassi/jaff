"""Low-level reaction network file parser for multiple astrochemical formats.

``NetworkParser`` reads a single network file and converts each reaction line
into a format-independent ``parsedListProps`` dict with keys:

- ``"r"``      — list of reactant name strings
- ``"p"``      — list of product name strings
- ``"tmin"``   — lower temperature bound in Kelvin, or ``None``
- ``"tmax"``   — upper temperature bound in Kelvin, or ``None``
- ``"rate"``   — rate expression as a Python/SymPy-compatible string
- ``"string"`` — the original network-file line (for error reporting)

Supported file formats
----------------------
The parser auto-detects the format from line patterns.  Each format is a
self-contained plugin under ``parsers.network._formats``; the engine discovers
them through :func:`~.parsers.network._formats.all_formats`, which orders them
by their declared ``priority`` (lower is matched first):

1. **PRIZMO** — arrow-notation (``->``) with optional temperature range in
   ``[tmin, tmax]`` brackets.  Variables in a ``VARIABLES { }`` block.
2. **UDFA** — colon-delimited, fixed-column database from the UMIST project.
3. **KROME** — comma-separated, declared via ``@format:`` header.
   Variable aliases via ``@var:``.
4. **UCLCHEM** — comma-separated with a ``NAN`` sentinel, includes grain
   surface reactions.
5. **KIDA** — fixed-width column format from the KIDA database.

Rate normalization
------------------
After parsing, all rate strings are lower-cased.  Known format-specific
symbols (``user_crflux``, ``user_av``, Fortran exponent notation ``d``,
temperature shortcuts ``t32``, ``invtgas``, etc.) are replaced with canonical
JAFF symbols before the strings are passed to SymPy for sympification.
"""

import logging
from pathlib import Path

from sympy import Basic, parse_expr

from ....common import resolve_symbolic_dependencies
from ....io import JaffLogger, jaff_progress
from ._typing import parsedListProps
from ._formats import (
    NetworkFormat,
    ParseContext,
    all_formats,
    build_state,
)


class NetworkParser:
    """Auto-detecting parser for astrochemical reaction network files.

    On construction the file is read, reactions are extracted, and rate
    strings are normalised.  Use as a context manager to ensure internal
    pattern state is freed after use.

    Parameters
    ----------
    file : str | Path
        Path to the network file.
    logger : logging.Logger | None, optional
        Logger instance.  A new JAFF logger is created if ``None``.

    Raises
    ------
    ValueError
        If *file* is not a ``str`` or ``Path``.
    FileNotFoundError
        If *file* does not exist on disk.
    ParserError
        On syntax errors encountered while parsing the file.
    """

    def __init__(self, file: str | Path, logger: logging.Logger | None = None):
        """Parse *file* and prepare the internal parsed-reaction list.

        Parameters
        ----------
        file : str | Path
            Path to the network file.
        logger : logging.Logger | None, optional
            External logger.  Defaults to a new JAFF logger.
        """
        if isinstance(file, str):
            file = Path(file)
        if not isinstance(file, (str, Path)):
            raise ValueError(f"Invalid file type detected for {file}: {type(file)}")

        file = file.resolve()
        if not file.exists():
            raise FileNotFoundError(file)

        self.__file: Path = file
        self.__logger: logging.Logger = logger or JaffLogger().get_logger()
        self.__globals: dict[str, Basic] = {}
        # Pre-populate well-known Fortran/KROME shorthand symbols as SymPy aliases.
        self.__set_known_replacments()

        self.__parsed_list: list[parsedListProps] = []
        self.__formats: list[NetworkFormat] = all_formats()
        self.__ctx: ParseContext = ParseContext(
            self.__file,
            self.__logger,
            self.__globals,
            self.__parsed_list,
            build_state(self.__formats),
        )

        self.__parse_file()
        self.__normalize_rates()
        self.__globals = resolve_symbolic_dependencies(self.__globals, fname=self.__file)

    def __enter__(self) -> "NetworkParser":
        """Return self when entering a ``with`` block.

        Returns
        -------
        NetworkParser
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Free the registered format plugins on context manager exit."""
        self.__formats.clear()

        return

    def get_parsed(self) -> tuple[list[parsedListProps], dict[str, Basic]]:
        """Return the parsed reaction list and resolved global variable map.

        Returns
        -------
        tuple[list[parsedListProps], dict[str, Basic]]
            - ``list[parsedListProps]``: one dict per reaction with keys
              ``"r"``, ``"p"``, ``"tmin"``, ``"tmax"``, ``"rate"``,
              ``"string"``.
            - ``dict[str, Basic]``: global symbolic constants defined in the
              file (e.g. ``@var`` entries), with all inter-dependencies
              resolved via SymPy substitution.
        """
        return self.__parsed_list, resolve_symbolic_dependencies(
            dep_map=self.__globals, fname=self.__file
        )

    def __parse_file(self) -> None:
        """Read the network file line-by-line and dispatch each line for parsing.

        Iterates over every line of :attr:`__file`, advancing the line counter
        and calling :meth:`__parse_line` for each.
        """
        with open(self.__file, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(
                jaff_progress.track(lines, description=f"Parsing {self.__file.name}")
            ):
                self.__ctx.nline = i + 1
                self.__ctx.line = line
                self.__parse_line()

    def __parse_line(self) -> None:
        """Match the current line against all known formats and invoke the handler.

        Iterates through :attr:`__formats` in priority order.  The first format
        whose global regex matches handles the line.  If no format matches the
        line is silently skipped.
        """
        if not self.__ctx.line.strip():
            return
        for fmt in self.__formats:
            if match := fmt._global_re(self.__ctx).match(self.__ctx.line):
                fmt.handle(match, self.__ctx)
                break

    def __set_known_replacments(self) -> None:
        """Pre-populate ``__globals`` with canonical JAFF symbol aliases.

        Inserts SymPy expressions for common KROME/PRIZMO shorthand variables
        such as ``t32``, ``te``, ``invtgas``, and ``sqrtgas`` so that they are
        resolved automatically during rate normalization.
        """
        # Populate __globals with canonical SymPy aliases for common shorthand
        # symbols found in KROME/PRIZMO files.  Order matters: compound aliases
        # (invt32, invte) must be listed before the simpler ones they depend on
        # so that resolve_symbolic_dependencies can substitute correctly.
        replacements = {
            "invt32": "1e0 / t32",
            "invte": "1e0 / te",
            "t32": "tgas/3e2",
            "te": "tgas*8.617343e-5",
            "invtgas": "1e0 / tgas",
            "sqrtgas": "sqrt(tgas)",
            "user_tdust": "tdust",
            "user_av": "av",
            "get_hnuclei(n)": "nh",
            "n(idx_h2)": "nh2",
            "n(idx_h)": "nh0",
            "n_global(idx_h2)": "nh2",
        }

        for k, v in replacements.items():
            self.__globals[k] = parse_expr(v)

    def __normalize_rates(self):
        """Lower-case all rate strings so SymPy ``parse_expr`` is case-insensitive."""
        for r in self.__parsed_list:
            assert isinstance(r["rate"], str)
            r["rate"] = r["rate"].lower()
