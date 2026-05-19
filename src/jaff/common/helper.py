from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from sympy import Basic, Piecewise
from sympy.core.function import AppliedUndef

from ..errors import ParserError

if TYPE_CHECKING:
    from ..auxilary_file_parser import FunctionsDict

HDF_EXTENSIONS = [".hdf5", ".hdf", ".h5"]
CSV_EXTENSIONS = [".csv", ".txt", ".dat"]
C_EXTENSIONS = [".c", ".h"]
CPP_EXTENSIONS = [".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"]
FORTRAN_EXTENSIONS = [".f", ".f90", ".f95", ".f03", ".f08", ".for", ".f77"]
RUST_EXTENSIONS = [".rs"]

F90_PATTERN = re.compile(r"([0-9_.])d([0-9_+-])")

ElementProps = TypedDict(
    "ElementProps",
    {
        "name": str,
        "mass": float,
        "atomic_mass": float,
        "protons": int,
        "neutrons": int,
        "electrons": int,
    },
)


def load_mass_dict() -> dict:
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
    expr = expr.replace("dexp(", "exp(").replace("(:)", "")

    return F90_PATTERN.sub(r"\1e\2", expr)


def resolve_symbolic_dependencies(
    dep_map: dict[str, Basic],
    external_refs: dict[str, Basic] | None = None,
    fname: Path | str = "",
) -> dict[str, Basic]:

    resolved = {}
    visiting = set()
    external = external_refs or {}

    def dfs(sym: str):
        if sym in resolved:
            return resolved[sym]

        if sym in external and sym not in dep_map:
            return external[sym]

        if sym in visiting:
            raise ParserError(f"Cyclic dependency found for {sym}", fname=fname)

        visiting.add(sym)
        expr = dep_map[sym]

        replacements = {}

        for s in expr.free_symbols:
            s_name = str(s)
            if s_name in dep_map or s_name in external:
                replacements[s] = dfs(s_name)

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
    if subs_dict is None:
        subs_dict = {}
    if aux_funcs is None:
        aux_funcs = {}

    for f in expr.atoms(AppliedUndef):
        name = f.func.__name__.lower()

        for k, v in subs_dict.items():
            if str(k).lower() == str(f).lower():
                subs_dict[f] = v
                break

        if name == "merge":
            subs_dict[f] = Piecewise(
                (f.args[0], f.args[2]),
                (f.args[1], True),
            )

        elif name == "log10":
            import sympy

            subs_dict[f] = sympy.log(f.args[0]) / sympy.log(10)

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
    return file.suffix.lower() == ".jaff" or [fn.lower() for fn in file.suffixes] == [
        ".jaff",
        ".gz",
    ]
