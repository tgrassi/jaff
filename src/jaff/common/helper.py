from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from sympy import Basic, Piecewise
from sympy.core.function import AppliedUndef

from ..errors.parser import ParserError

if TYPE_CHECKING:
    from ..auxilary_file_parser import FunctionsDict

F90_PATTERN = re.compile(r"([0-9_.])d([0-9_+-])")


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
