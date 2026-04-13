import numpy as np
from scipy.integrate import quad, simpson, trapezoid
from sympy import Basic, Expr, FiniteSet, lambdify, piecewise_fold, solve
from sympy.core.relational import Relational


def integrate(
    expr: Basic | Expr,
    sym: Basic,
    bounds: tuple[float | int, float | int],
    integrator: str = "trapezoid",
    spacing: str = "lin",
):
    integrators = {"trapezoid": trapezoid, "simpson": simpson}
    spacings = {"lin": np.linspace, "log": np.logspace}

    if integrator not in integrators:
        raise ValueError(
            f"Invalid integrator specified: {integrator}\n"
            f"Supported integrators are {integrators.keys()}"
        )
    if spacing not in spacings:
        raise ValueError(
            f"Invalid spacing specified: {spacing}\n"
            f"Supported spacings are {spacings.keys()}"
        )

    lower, upper = bounds
    samples = spacings[spacing](lower, upper, 1_000_000)
    func = lambdify(sym, expr, "numpy")

    return integrators[integrator](func(samples), samples)


def get_bounds(expr: Basic, sym: Basic):
    folded = piecewise_fold(expr)
    boundaries = set()

    if hasattr(folded, "as_expr_set_pairs"):
        for val, domain in folded.as_expr_set_pairs():
            if val == 0:
                continue

            b = domain.boundary
            if not isinstance(b, FiniteSet):
                continue

            for pt in b:
                boundaries.add(float(pt))

    if not boundaries:
        for rel in folded.atoms(Relational):
            try:
                cp = solve(rel.lhs - rel.rhs, sym)
                for p in cp:
                    if p.is_real:
                        boundaries.add(float(p))
            except Exception:
                continue

    return sorted(list(boundaries))


def smart_integrate(
    expr: Basic, sym: Basic, bounds: tuple[float | int | Basic, float | int | Basic]
):
    lower, upper = bounds

    folded = piecewise_fold(expr)
    f_num = lambdify(sym, folded, "numpy")
    pts = get_bounds(folded, sym)

    t_low = float(lower) if not isinstance(lower, Basic) else -np.inf
    t_high = float(upper) if not isinstance(upper, Basic) else np.inf

    a, b = t_low, t_high
    if pts:
        a = max(t_low, min(pts))
        b = min(t_high, max(pts))

    if a >= b:
        return 0.0

    sub_points = []

    if a > 0 and not np.isinf(b) and b > a:
        decades = np.log10(b) - np.log10(a)
        if decades > 0.1:
            log_pts = np.logspace(np.log10(a), np.log10(b), int(decades * 5) + 2)
            sub_points.extend(log_pts[1:-1])  # Exclude the boundaries a and b

    internal_bounds = [p for p in pts if a < p < b]
    sub_points.extend(internal_bounds)

    sub_points = sorted(list(set(sub_points)))

    if np.isinf(a) or np.isinf(b):
        val, _ = quad(f_num, a, b, limit=10000)

        return val

    val, _ = quad(f_num, a, b, points=sub_points, limit=200)

    return val


def safe_integrate():
    raise NotImplementedError("Not yet implemented")
