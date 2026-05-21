# ABOUTME: Unit tests for SymPy JSON serialization
# ABOUTME: Ensures deterministic round-tripping for supported node types

import os
import sys

import pytest
import sympy

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jaff.common._sympy_json import dumps, from_jsonable, loads, to_jsonable


def _rt(expr: sympy.Basic) -> sympy.Basic:
    return loads(dumps(expr))


def test_roundtrip_basic_arithmetic_and_numbers():
    x = sympy.Symbol("x", real=True)
    y = sympy.Symbol("y")
    expr = sympy.Add(
        sympy.Integer(2),
        sympy.Rational(1, 3),
        sympy.Float("1.0e-10"),
        x * y,
        evaluate=False,
    )

    expr2 = _rt(expr)
    diff = sympy.simplify(expr2 - expr)
    assert abs(float(diff.evalf())) < 1e-15
    x2 = next(s for s in expr2.free_symbols if s.name == "x")
    assert x2.assumptions0.get("real", None) is True


def test_roundtrip_commutative_order_is_deterministic():
    x = sympy.Symbol("x")
    y = sympy.Symbol("y")
    expr1 = sympy.Add(x, y, sympy.Integer(1), evaluate=False)
    expr2 = sympy.Add(y, sympy.Integer(1), x, evaluate=False)

    j1 = dumps(expr1)
    j2 = dumps(expr2)
    assert j1 != j2
    assert loads(j1) == expr1
    assert loads(j2) == expr2


def test_roundtrip_piecewise_strict_lessthan():
    x = sympy.Symbol("x")
    pw = sympy.Piecewise(
        (x, sympy.StrictLessThan(x, sympy.Integer(0))),
        (sympy.Integer(0), sympy.true),
        evaluate=False,
    )
    pw2 = _rt(pw)
    assert pw2 == pw


def test_roundtrip_min_max_log_exp_pow_mul():
    x = sympy.Symbol("x")
    expr = sympy.Mul(
        sympy.Max(x, sympy.Integer(1), evaluate=False),
        sympy.Min(x, sympy.Integer(2), evaluate=False),
        sympy.exp(x),
        sympy.log(sympy.Integer(10)),
        sympy.Pow(x, sympy.Integer(2), evaluate=False),
        evaluate=False,
    )
    expr2 = _rt(expr)
    assert expr2 == expr


def test_roundtrip_matrix_symbol_and_element():
    nden = sympy.MatrixSymbol("nden", sympy.Integer(3), sympy.Integer(1))
    expr = nden[0, 0] + nden[2, 0]
    expr2 = _rt(expr)
    assert expr2 == expr


def test_direct_jsonable_api_roundtrip():
    x = sympy.Symbol("x", positive=True)
    expr = sympy.Add(sympy.Integer(1), sympy.exp(x), evaluate=False)
    node = to_jsonable(expr)
    expr2 = from_jsonable(node)
    assert expr2 == expr


def test_compact_float_is_number():
    expr = sympy.Add(sympy.Float("2.0e-12"), sympy.Float("1.5"), evaluate=False)
    node = to_jsonable(expr)
    assert isinstance(node, list)
    assert node[0] == "Add"
    args = node[1]
    assert isinstance(args, list)
    assert all(isinstance(arg, (int, float)) for arg in args)
    expr2 = from_jsonable(node)
    diff = sympy.simplify(expr2 - expr)
    assert abs(float(diff.evalf())) < 1e-15
