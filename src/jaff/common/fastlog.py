#!/usr/bin/env python3

"""
This module implements fast log utility functions. The code here is heavily borrowed from https://github.com/quokka-astro/quokka/.
"""

import numpy as np
from scipy.optimize import root_scalar


def fast_log2(x):
    """
    Fast approximation of log2(x) using the not-quite-logarithmic method.

    Parameters
    ----------
        x : float or arraylike
            Value(s) for which to compute fastlog

    Returns
    -------
        logx : float or array
            Approximation of log2(x)
    """

    # Handle scalar or array inputs
    x_ = np.asarray(x)
    scalar_input = x_.ndim == 0
    x_ = np.atleast_1d(x_)

    # frexp returns (mantissa, exponent) where x = mantissa * 2^exponent
    # and 0.5 <= mantissa < 1.0
    mantissa, exponent = np.frexp(x_)

    # The not-quite-log approximation: log2(x) ≈ 2(mantissa - 1) + exponent
    res = 2 * (mantissa - 1) + exponent

    # Handle negative arguments
    res[x_ <= 0.0] = np.nan

    # Make output type match input type
    if scalar_input:
        return res[0]
    else:
        return res


def inverse_fast_log2(y):
    """
    Compute the numerical inverse of fast_log2 to machine precision

    Parameters
    ----------
        y : float or arraylike
            The value(s) for which to find the inverse fast_log2

    Returns
    -------
        x : float or array
            The value of x such that fast_log2(x) = y to machine precision
    """

    # Set up storage for result
    y_arr = np.atleast_1d(y)
    res = np.zeros(y_arr.shape)

    # Set accuracy goal
    eps = np.finfo(np.float64).eps

    # Loop over input values
    for i, y_ in enumerate(y_arr):
        # Set initial guess to inverse of exact log_2(x) function
        x_guess = 2.0**y_

        # Bracket the root by factors of 2 on either side; bracketing is
        # guaranteed to be safe because fast_log2 is monotonic
        x_bracket = np.array([0.5, 2]) * x_guess

        # Search for root using Brent's method
        root = root_scalar(
            lambda x: fast_log2(x) - y_,
            method="brentq",
            bracket=x_bracket,
            xtol=eps * x_guess,
            rtol=4 * eps,
            maxiter=1000,
        )

        # Check that we have achieved target tolerance
        resid = abs(fast_log2(root.root) - y_)
        tol = eps * abs(y_) * 20
        if resid > tol:
            # If we are here, we have not hit the target tolerance, so
            # try to polish the root by taking five Netwon iteration steps
            for _ in range(5):
                dx = -(fast_log2(root.root) - y_) * root.root * np.log(2)
                root_new = root.root + dx
                resid_new = abs(fast_log2(root_new) - y_)
                if resid_new < resid:
                    root.root = root_new
                    resid = resid_new
                else:
                    break

            # Warn if final residual too high
            if resid > tol:
                print(
                    "Warning: could not reduce residual below {:e} for "
                    "inverse_fast_log2({:e})".format(resid, y_)
                )

        # Store result
        res[i] = root.root

    # Return output of correct dimensionality
    if np.asarray(y).ndim == 0:
        return res[0]
    else:
        return res
