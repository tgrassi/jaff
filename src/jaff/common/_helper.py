"""
Miscellaneous helper utilities shared across JAFF subsystems.

This module provides:

* Extension-list constants for recognizing source/data file types.
* :func:`load_mass_dict` -- load atomic masses from the embedded SQLite DB.
* :func:`f90_convert` -- coerce Fortran-style numeric literals to Python/C.
* :func:`resolve_symbolic_dependencies` -- topological substitution of a
  symbol dependency graph.
* :func:`resolve_dependencies` -- single-expression dependency resolution
  with special handling for built-in JAFF functions (``merge``, ``log10``).
* :func:`is_jaff_file` -- quick path-based check for ``.jaff`` files.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import TYPE_CHECKING

from sympy import Basic, Piecewise
from sympy.core.function import AppliedUndef

from ..errors import ParserError

if TYPE_CHECKING:
    from ..core._auxiliary_engine import FunctionsDict
    from ..core._typing import ElementProps

# ---------------------------------------------------------------------------
# File-extension groups used by parsers and code generators
# ---------------------------------------------------------------------------

HDF_EXTENSIONS = [".hdf5", ".hdf", ".h5"]
CSV_EXTENSIONS = [".csv", ".txt", ".dat"]
C_EXTENSIONS = [".c", ".h"]
CPP_EXTENSIONS = [".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"]
FORTRAN_EXTENSIONS = [".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77"]
RUST_EXTENSIONS = [".rs"]

# Matches Fortran double-precision exponent notation, e.g. ``1.0d-3`` → ``1.0e-3``
F90_PATTERN = re.compile(r"([0-9_.])d([0-9_+-])")


def load_mass_dict() -> dict:
    """
    Load atomic mass data from the JAFF embedded SQLite database.

    Opens the bundled ``atomic_masses`` table via :class:`~jaff.drivers.sqlite.JaffDb`
    and returns a dict keyed by element symbol.

    Returns
    -------
    dict[str, ElementProps]
        Mapping from element symbol (e.g. ``"H"``) to an
        :class:`~jaff.core._typing.ElementProps` dict with keys
        ``name``, ``mass``, ``atomic_mass``, ``protons``, ``neutrons``,
        and ``electrons``.
    """
    from ..drivers.sqlite import JaffDb

    with JaffDb() as jdb:
        rows = jdb.table("atomic_masses").all_rows()

    mass_dict: dict[str, ElementProps] = {}
    for row in rows:
        mass_dict[row["element"]] = {
            "name": row["name"],
            "mass": row["mass"],
            "atomic_mass": row["atomic_mass"],
            "protons": row["protons"],
            "neutrons": row["neutrons"],
            "electrons": row["electrons"],
        }

    return mass_dict


def f90_convert(expr: str) -> str:
    """
    Convert a Fortran-style numeric expression string to Python/C syntax.

    Applies three transformations:

    1. Replaces ``dexp(`` with ``exp(`` (Fortran intrinsic → standard name).
    2. Replaces the Fortran double-precision exponent marker ``d`` with ``e``
       in numeric literals (e.g. ``1.0d-3`` → ``1.0e-3``), using
       :data:`F90_PATTERN`.
    3. Removes Fortran array subscript notation ``(:)`` which has no meaning
       in a scalar expression context.

    Parameters
    ----------
    expr : str
        The expression string to convert.

    Returns
    -------
    str
        The converted expression string.
    """
    expr = expr.replace("dexp(", "exp(").replace("(:)", "")

    return F90_PATTERN.sub(r"\1e\2", expr)


def resolve_symbolic_dependencies(
    dep_map: dict[str, Basic],
    external_refs: dict[str, Basic] | None = None,
    fname: Path | str = "",
) -> dict[str, Basic]:
    """
    Topologically resolve a symbol dependency graph into fully-substituted expressions.

    Given a mapping from symbol names to SymPy expressions that may reference
    other symbols in the same mapping, this function performs a depth-first
    traversal and returns a new mapping where every expression has all
    internal dependencies substituted away.  Symbols present in
    *external_refs* but not in *dep_map* are treated as resolved leaf values.

    Parameters
    ----------
    dep_map : dict[str, sympy.Basic]
        Mapping from symbol name to its defining expression.  Expressions may
        contain references to other keys in this dict or to keys in
        *external_refs*.
    external_refs : dict[str, sympy.Basic] or None, optional
        Additional pre-resolved symbol definitions.  When a name appears in
        both *external_refs* and *dep_map*, the local *dep_map* definition
        takes precedence.
    fname : pathlib.Path or str, optional
        Source file path shown in error messages (default ``""``).

    Returns
    -------
    dict[str, sympy.Basic]
        A new dict with the same keys as *dep_map* but with all internal
        symbol references expanded to their final values.

    Raises
    ------
    ParserError
        If a cyclic dependency is detected (e.g. ``A`` depends on ``B``
        which depends on ``A``).

    Notes
    -----
    Both free :class:`sympy.Symbol` objects and undefined applied functions
    (:class:`sympy.core.function.AppliedUndef`) are considered dependencies
    and resolved recursively.
    """
    resolved = {}
    visiting = set()
    external = external_refs or {}

    def dfs(sym: str):
        """Recursively resolve *sym*, memoizing results in *resolved*."""
        if sym in resolved:
            return resolved[sym]

        if sym in external and sym not in dep_map:
            return external[sym]

        if sym in visiting:
            raise ParserError(f"Cyclic dependency found for {sym}", fname=fname)

        visiting.add(sym)
        expr = dep_map[sym]

        replacements = {}

        # Resolve free symbol references (e.g. plain ``tgas`` in the expression)
        for s in expr.free_symbols:
            s_name = str(s)
            if s_name in dep_map or s_name in external:
                replacements[s] = dfs(s_name)

        # Resolve applied undefined function references (e.g. ``f(x)`` where
        # ``f`` is a user-defined auxiliary function)
        for f in expr.atoms(AppliedUndef):
            f_str = str(f)

            if f_str in dep_map or f_str in external:
                replacements[f] = dfs(f_str)
            else:
                f_name = f.func.__name__
                if f_name in dep_map or f_name in external:
                    replacements[f] = dfs(f_name)

        new_expr = expr.xreplace(replacements)

        visiting.remove(sym)
        resolved[sym] = new_expr

        return new_expr

    return {sym: dfs(sym) for sym in dep_map}


def resolve_dependencies(
    expr: Basic,
    subs_dict: dict[Basic, Basic] | None = None,
    aux_funcs: dict[str, FunctionsDict] | None = None,
) -> Basic:
    """
    Resolve undefined SymPy function calls inside a single expression.

    Walks all :class:`~sympy.core.function.AppliedUndef` atoms in *expr* and
    replaces each with a concrete SymPy expression, drawing from three sources
    (checked in priority order):

    1. **subs_dict** -- direct substitution table.
    2. **Built-in shims** -- ``merge(a, b, cond)`` → ``Piecewise((a, cond), (b, True))``
       and ``log10(x)`` → ``log(x)/log(10)``.
    3. **aux_funcs** -- user-defined auxiliary functions provided by the
       parser; arguments are recursively resolved before substitution.

    Parameters
    ----------
    expr : sympy.Basic
        The expression in which to resolve dependencies.
    subs_dict : dict[sympy.Basic, sympy.Basic] or None, optional
        Pre-populated substitution table.  Modified in-place as new
        substitutions are discovered.  Defaults to an empty dict.
    aux_funcs : dict[str, FunctionsDict] or None, optional
        Auxiliary function definitions keyed by lowercase function name.
        Each entry must have ``"def"`` (the body expression) and ``"args"``
        (the ordered parameter list).  Defaults to an empty dict.

    Returns
    -------
    sympy.Basic
        The expression with all recognized undefined function calls replaced.
        Unrecognized functions are left unchanged.
    """
    if subs_dict is None:
        subs_dict = {}
    if aux_funcs is None:
        aux_funcs = {}

    for f in expr.atoms(AppliedUndef):
        name = f.func.__name__.lower()

        # Check the direct substitution table first (case-insensitive key match)
        for k, v in subs_dict.items():
            if str(k).lower() == str(f).lower():
                subs_dict[f] = v
                break

        # Built-in: ``merge(a, b, cond)`` → Piecewise
        if name == "merge":
            subs_dict[f] = Piecewise(
                (f.args[0], f.args[2]),
                (f.args[1], True),
            )

        # Built-in: ``log10(x)`` → sympy natural-log form
        elif name == "log10":
            import sympy

            subs_dict[f] = sympy.log(f.args[0]) / sympy.log(10)

        # User-defined auxiliary function: inline-expand with argument mapping
        elif name in aux_funcs:
            func_def = aux_funcs[name]["def"]
            func_args = aux_funcs[name]["args"]

            arg_map = dict(
                zip(
                    func_args,
                    [resolve_dependencies(arg, subs_dict, aux_funcs) for arg in f.args],
                )
            )

            subs_dict[f] = func_def.xreplace(arg_map)

    expr = expr.xreplace(subs_dict)

    return expr


def is_jaff_file(file: Path) -> bool:
    """
    Return ``True`` if *file* has a ``.jaff`` or ``.jaff.gz`` extension.

    The check is case-insensitive.

    Parameters
    ----------
    file : pathlib.Path
        The path to test.

    Returns
    -------
    bool
        ``True`` iff the path ends with ``.jaff`` or ``.jaff.gz``.
    """
    return file.suffix.lower() == ".jaff" or [fn.lower() for fn in file.suffixes] == [
        ".jaff",
        ".gz",
    ]


def load_module_from_path(path: str | Path, module_name: str):
    mpath: Path = path  # type: ignore
    if isinstance(path, str):
        mpath = Path(path).resolve()

    spec = importlib.util.spec_from_file_location(module_name, mpath)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {mpath}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module
