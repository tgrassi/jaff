import numpy as np
from sympy import Expr, Max, Symbol, exp


def shielding(
    alpha: int | float, min_ncol: float = 1.0e-50, min_vdisp: float = 1.0e-50
) -> Expr:
    # min_vdisp : unit cm/s
    # min_ncol : unit cm^-2

    N2 = Symbol("ncol_H2")
    b = np.sqrt(2) * Symbol("vdisp")

    x = Max(N2 / 5.0e14, min_ncol)
    b5 = Max(b / 1.0e5, min_vdisp)

    f1 = 0.965 / (1.0 + x / b5) ** alpha
    f2 = 0.035 / (1 + x) ** 0.5
    f3 = exp(-8.5e-4 * (1.0 + x) ** 0.5)

    return f1 + f2 * f3
