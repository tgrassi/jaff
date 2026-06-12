"""
Numerical integration helpers for SymPy expressions.

This module provides three utilities:

* :func:`integrate` -- fixed-sample quadrature (trapezoid or Simpson) via
  :func:`sympy.lambdify`, for use when a quick approximate answer is needed.
* :func:`get_bounds` -- extract breakpoints (discontinuities / kinks) from a
  piecewise SymPy expression so that adaptive integrators can avoid them.
* :func:`smart_integrate` -- adaptive quadrature via :func:`scipy.integrate.quad`
  that handles piecewise expressions, symbolic infinity bounds, and
  multi-decade ranges.
"""

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
    """
    Numerically integrate a SymPy expression using fixed-sample quadrature.

    The expression is converted to a NumPy function via
    :func:`sympy.lambdify` and then evaluated on a uniform or logarithmically
    spaced grid of 1 000 000 points before applying the chosen quadrature
    rule.

    Parameters
    ----------
    expr : sympy.Basic or sympy.Expr
        The expression to integrate.
    sym : sympy.Basic
        The integration variable.
    bounds : tuple of (float or int, float or int)
        Integration interval ``(lower, upper)``.
    integrator : {"trapezoid", "simpson"}, optional
        Quadrature rule to apply (default ``"trapezoid"``).
    spacing : {"lin", "log"}, optional
        Sample-point spacing: ``"lin"`` for linear (default) or ``"log"`` for
        logarithmic.

    Returns
    -------
    float
        The approximate definite integral.

    Raises
    ------
    ValueError
        If *integrator* or *spacing* is not one of the supported options.
    """
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
    """
    Extract breakpoints of a piecewise SymPy expression as floats.

    Uses two strategies in order:

    1. **Domain boundaries** -- calls :func:`sympy.piecewise_fold` then
       iterates over ``(value, domain)`` pairs; for each non-zero value, the
       domain's boundary :class:`~sympy.sets.sets.FiniteSet` is collected.
    2. **Relational atoms** -- if no boundaries were found by strategy 1,
       solves each :class:`~sympy.core.relational.Relational` atom for *sym*
       to recover implicit breakpoints.

    Parameters
    ----------
    expr : sympy.Basic
        A piecewise (or potentially piecewise) SymPy expression.
    sym : sympy.Basic
        The variable with respect to which breakpoints are identified.

    Returns
    -------
    list of float
        Sorted list of distinct breakpoint values.  Empty if no breakpoints
        were found.
    """
    folded = piecewise_fold(expr)
    boundaries = set()

    # Strategy 1: read breakpoints directly from domain boundary sets
    if hasattr(folded, "as_expr_set_pairs"):
        for val, domain in folded.as_expr_set_pairs():
            if val == 0:
                continue

            b = domain.boundary
            if not isinstance(b, FiniteSet):
                continue

            for pt in b:
                boundaries.add(float(pt))

    # Strategy 2: solve relational conditions for sym when strategy 1 found nothing
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
) -> float:
    """
    Adaptively integrate a (piecewise) SymPy expression over a possibly symbolic interval.

    Handles several complications that trip up naive quadrature:

    * **Piecewise expressions** -- :func:`sympy.piecewise_fold` is applied and
      breakpoints are extracted via :func:`get_bounds`; they are then passed to
      :func:`scipy.integrate.quad` as the ``points`` argument so the integrator
      can straddle discontinuities.
    * **Symbolic bounds** -- if *lower* or *upper* are SymPy
      :class:`~sympy.core.basic.Basic` objects (e.g. ``-oo`` / ``oo``)
      they are mapped to ``-np.inf`` / ``np.inf``.
    * **Multi-decade ranges** -- when the effective integration domain spans
      more than 0.1 decades in log10 space, logarithmically spaced interior
      sample hints are added to ``points`` to help the adaptive routine resolve
      steep rate curves.

    Parameters
    ----------
    expr : sympy.Basic
        The expression to integrate.
    sym : sympy.Basic
        The integration variable.
    bounds : tuple of (float or int or sympy.Basic, float or int or sympy.Basic)
        Integration interval ``(lower, upper)``.  Symbolic values are
        interpreted as ``±inf``.

    Returns
    -------
    float
        The approximate definite integral.  Returns ``0.0`` immediately if
        the effective integration interval is empty (``a >= b``).

    Notes
    -----
    When the interval contains infinities, :func:`scipy.integrate.quad` is
    called with ``limit=10000`` and no interior ``points`` hint (because
    ``quad`` does not accept ``points`` with infinite bounds).  For finite
    intervals ``limit=200`` is used.
    """
    lower, upper = bounds

    folded = piecewise_fold(expr)
    f_num = lambdify(sym, folded, "numpy")
    pts = get_bounds(folded, sym)

    # Resolve symbolic bounds to float ±inf
    t_low = float(lower) if not isinstance(lower, Basic) else -np.inf
    t_high = float(upper) if not isinstance(upper, Basic) else np.inf

    # Clip the integration domain to the range covered by piecewise breakpoints
    a, b = t_low, t_high
    if pts:
        a = max(t_low, min(pts))
        b = min(t_high, max(pts))

    if a >= b:
        return 0.0

    sub_points = []

    # Add log-spaced interior hints when the domain spans >0.1 decades
    if a > 0 and not np.isinf(b) and b > a:
        decades = np.log10(b) - np.log10(a)
        if decades > 0.1:
            log_pts = np.logspace(np.log10(a), np.log10(b), int(decades * 5) + 2)
            sub_points.extend(log_pts[1:-1])  # Exclude the boundaries a and b

    # Add piecewise breakpoints that fall strictly inside [a, b]
    internal_bounds = [p for p in pts if a < p < b]
    sub_points.extend(internal_bounds)

    sub_points = sorted(list(set(sub_points)))

    # quad does not accept the ``points`` argument when bounds are infinite
    if np.isinf(a) or np.isinf(b):
        val, _ = quad(f_num, a, b, limit=10000)

        return val

    val, _ = quad(f_num, a, b, points=sub_points, limit=200)

    return val


def arr_integrate(
    y: np.ndarray, x: np.ndarray, bounds: tuple[float | int | Basic, float | int | Basic]
) -> float:
    """
    Trapezoidal integral of tabulated data ``y(x)`` over an interval.

    Used for cross-section integrals where ``σ(E)`` is only known as sampled
    ``(E, σ)`` arrays, so a closed form is unavailable.

    Parameters
    ----------
    y : numpy.ndarray
        Sampled integrand values, aligned with ``x``.
    x : numpy.ndarray
        Sample abscissae, assumed sorted ascending.
    bounds : tuple
        ``(lower, upper)`` integration limits.  A non-symbolic bound is used
        as-is; a symbolic (:class:`sympy.Basic`) bound is treated as ``±inf``,
        i.e. the open end of the tabulated range.  Both limits are clamped to
        ``[x[0], x[-1]]``.

    Returns
    -------
    float
        The integral, or ``0.0`` if the clamped interval is empty.

    Notes
    -----
    The endpoints are inserted into the sample grid via linear interpolation
    so the integral covers exactly ``[lower, upper]`` rather than the nearest
    sample points.
    """
    # Assumes data is sorted (ascending in x).
    lower, upper = bounds
    t_low = float(lower) if not isinstance(lower, Basic) else -np.inf
    t_high = float(upper) if not isinstance(upper, Basic) else np.inf

    t_low = max(t_low, x[0])
    t_high = min(t_high, x[-1])
    if t_high <= t_low:
        return 0.0

    i_low = np.searchsorted(x, t_low)
    i_high = np.searchsorted(x, t_high)

    x_seg = x[i_low:i_high]
    y_seg = y[i_low:i_high]

    x_seg = np.r_[t_low, x_seg, t_high]
    y_seg = np.r_[np.interp(t_low, x, y), y_seg, np.interp(t_high, x, y)]

    return np.trapezoid(y_seg, x_seg)


def safe_integrate():
    """
    Placeholder for a future robust integration routine.

    Raises
    ------
    NotImplementedError
        Always.  This function is not yet implemented.
    """
    raise NotImplementedError("Not yet implemented")
