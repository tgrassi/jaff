import re

F90_PATTERN = re.compile(r"([0-9_.])d([0-9_+-])")


def f90_convert(expr: str) -> str:
    expr = expr.replace("dexp(", "exp(").replace("(:)", "")

    return F90_PATTERN.sub(r"\1e\2", expr)
