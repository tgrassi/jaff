from functools import cached_property
from pathlib import Path
from tokenize import TokenError
from typing import Any, Callable, NotRequired, TypedDict

import sympy as sp
from sympy.core.function import AppliedUndef

from .errors.parser import ParserError

FunctionsDict = TypedDict(
    "FunctionsDict",
    {
        "def": sp.Basic,
        "args": list[sp.Basic],
        "argcomments": dict[str, str],
        "locals": NotRequired[dict[str, sp.Basic]],
    },
)


class AuxilaryFunctionParser:
    def __init__(self, file: Path | str):
        if not isinstance(file, (Path, str)):
            raise ValueError(
                f"Invalid file type detected: {file}\n"
                f"file must be a pathlib.Path object or a str"
            )
        if isinstance(file, str):
            file = Path(file)

        file = file.resolve()
        if not file.exists():
            raise FileNotFoundError(f"File cannot be read: {file}")

        self.file: Path = file
        self.og_line: str = ""
        self.line: str = ""
        self.cline: str = ""  # Continous line
        self.nline: int = 0
        self.globals: dict[str, sp.Basic] = {}
        self.globals_parsed: bool = False
        self.func_dict: dict[str, FunctionsDict] = {}
        self.scope: str = "global"  # global | func
        self.current_func: str = ""

        self.__parse_file()
        self.__resolve_func_deps()

    def __repr__(self):
        return f"AuxiliaryFunctionParserObject: {self.file}"

    def __str__(self):
        return f"AuxiliaryFunctionParserObject: {self.file}"

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.globals.clear()
        self.__dict__.clear()
        self.og_line = self.line = self.cline = ""

    def get_dict(self):
        return self.func_dict

    def __parse_file(self) -> None:
        with open(self.file, "r") as f:
            for nline, line in enumerate(f, start=1):
                self.nline = nline
                self.og_line = line.strip()

                if len(self.og_line) == 0:
                    continue

                if self.og_line.endswith("\\"):
                    self.cline += f"{self.og_line[:-1]} "
                    continue

                self.cline += line
                self.line = self.cline.strip()
                self.cline = ""
                self.__parse_line()

    def __parse_line(self) -> None:
        if self.scope == "function":
            self.__parse_function()

        if self.line.startswith("@"):
            self.parse = True
            self.__parse_token()

            return

        if self.line.startswith("#"):
            return

    def __parse_token(self):
        line = self.line[1:].strip()
        split_line: list[str] = line.split(maxsplit=1)
        token, segment = split_line[0], split_line[1]

        if token not in self.tokens:
            raise ParserError(
                f"Invalid token detected: @{token}", self.og_line, self.nline, self.file
            )

        self.tokens[token](self.__strip_trailing_comment(segment.strip())[0])

    def __set_scope(self, scope: str):
        self.scope = scope

    def __handle_var(self, segment: str) -> None:
        tokens: list[str] = segment.split("=", maxsplit=1)
        if len(tokens) != 2:
            raise ParserError(
                "Invalid variable encountered", self.og_line, self.nline, self.file
            )
        var, expr = tokens[0].strip(), tokens[1].strip()

        try:
            self.globals[str(var)] = sp.parse_expr(expr)
        except (SyntaxError, TokenError, TypeError, sp.SympifyError) as e:
            raise ParserError(
                f"Invalid expression encountered: {e}",
                self.og_line,
                self.nline,
                self.file,
            )

    def __handle_function_decleration(self, segment: str):
        self.__set_scope("function")
        if not self.globals_parsed:
            self.globals_parsed = True
            self.globals = self.__simplify_dep_map(self.globals)

        parts = segment.split("(", maxsplit=1)
        if len(parts) != 2:
            raise ParserError(
                "Invalid function decleration", self.og_line, self.nline, self.file
            )
        name, rest = parts[0].lower(), parts[1]
        rest = rest.split(")", maxsplit=1)

        if len(rest) != 2:
            raise ParserError(
                "Invalid function decleration", self.og_line, self.nline, self.file
            )
        args = [
            sp.parse_expr(arg.strip())
            for arg in rest[0].split(",")
            if len(arg.strip()) > 0
        ]

        self.current_func = name
        self.func_dict[name] = {
            "def": sp.Float(0.0),
            "args": [],
            "argcomments": {},
            "locals": {},
        }
        self.func_dict[name]["args"] = args

    def __parse_function(self):
        line = self.line
        if line.startswith("return"):
            self.__handle_function_return()
            return

        elif line.startswith("#"):
            self.__handle_function_comment()
            return

        line, _ = self.__strip_trailing_comment(line)
        splitline = line.split("=", maxsplit=1)

        if len(splitline) != 2:
            raise ParserError(
                "Invalid line detected", self.og_line, self.nline, self.file
            )

        var, expr = splitline[0].strip(), splitline[1].strip()
        try:
            self.func_dict[self.current_func]["locals"][str(var)] = sp.parse_expr(expr)
        except (SyntaxError, TokenError, TypeError, sp.SympifyError) as e:
            raise ParserError(
                f"Invalid expression encountered: {e}",
                self.og_line,
                self.nline,
                self.file,
            )

    def __handle_function_comment(self) -> None:
        line = self.line[1:].strip()
        split_line = line.split(maxsplit=1)

        if len(split_line) < 2:
            return

        arg, comment = split_line[0], split_line[1]
        if sp.Symbol(arg) in self.func_dict[self.current_func]["args"]:
            self.func_dict[self.current_func]["argcomments"][arg] = comment.strip()

    def __handle_function_return(self) -> None:
        line = self.line
        line, _ = self.__strip_trailing_comment(line)
        self.func_dict[self.current_func]["locals"] = self.__simplify_dep_map(
            self.func_dict[self.current_func]["locals"], external_refs=self.globals
        )

        try:
            funcdef = sp.parse_expr(
                line.lstrip("return").strip(),
                local_dict={
                    **self.globals,
                    **self.func_dict[self.current_func]["locals"],
                },
            )

            func_cache = {}
            funcdef = funcdef.xreplace(
                {
                    f: func_cache.setdefault(f.name.lower(), sp.Function(f.name.lower()))(
                        *f.args
                    )
                    for f in funcdef.atoms(AppliedUndef)
                }
            )
        except (SyntaxError, TokenError, TypeError, sp.SympifyError) as e:
            raise ParserError(
                f"Invalid expression encountered: {e}",
                self.og_line,
                self.nline,
                self.file,
            )

        self.func_dict[self.current_func]["def"] = funcdef
        self.func_dict[self.current_func].pop("locals")
        self.current_func = ""
        self.__set_scope("global")

    def __simplify_dep_map(
        self,
        dep_map: dict[str, sp.Basic],
        external_refs: dict[str, sp.Basic] | None = None,
    ):
        resolved = {}
        visiting = set()
        external = external_refs or {}

        def dfs(sym: str):
            if sym in resolved:
                return resolved[sym]

            if sym in external and sym not in dep_map:
                return external[sym]

            if sym in visiting:
                raise ParserError(f"Cyclic dependency found for {sym}", fname=self.file)

            visiting.add(sym)
            expr = dep_map[sym]
            new_expr = expr

            for s in expr.free_symbols:
                s_name = str(s)
                if s_name in dep_map or s_name in external:
                    new_expr = new_expr.subs(s, dfs(s_name))

            visiting.remove(sym)
            resolved[sym] = new_expr

            return new_expr

        return {sym: dfs(sym) for sym in dep_map}

    def __resolve_func_deps(self):
        resolved_defs = {}
        visiting = set()

        def dfs_resolve_func(name: str):
            if name in resolved_defs:
                return resolved_defs[name]

            if name in visiting:
                raise ParserError(
                    f"Circular function dependency: {name}", fname=self.file
                )

            visiting.add(name)

            f_data = self.func_dict[name]
            expr = f_data["def"]

            for func in expr.atoms(AppliedUndef):
                func_name = func.func.__name__.lower()
                if func_name in self.func_dict:
                    nested_f_def = dfs_resolve_func(func_name)
                    nested_f_args = self.func_dict[func_name]["args"]
                    arg_map = dict(zip(nested_f_args, func.args))
                    resolved_call = nested_f_def.subs(arg_map)
                    expr = expr.subs(func, resolved_call)

            visiting.remove(name)
            resolved_defs[name] = expr
            return expr

        for func_name in self.func_dict:
            self.func_dict[func_name]["def"] = dfs_resolve_func(func_name)

    @staticmethod
    def __strip_trailing_comment(line: str) -> tuple[str, str]:
        parts: list[str] = line.split("#", maxsplit=1)
        if len(parts) == 1:
            parts.append("")

        return parts[0], parts[1]

    @cached_property
    def tokens(self) -> dict[str, Callable[..., Any]]:
        names: dict[str, Callable[..., Any]] = {
            "var": self.__handle_var,
            "function": self.__handle_function_decleration,
        }

        return names


if __name__ == "__main__":
    import time

    start_time = time.perf_counter()
    afp = AuxilaryFunctionParser(Path("networks/GOW.dat_functions"))

    end_time = time.perf_counter()
    print(f"Execution time: {end_time - start_time:.6f} seconds")
