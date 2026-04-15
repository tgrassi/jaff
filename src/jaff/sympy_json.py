# ABOUTME: JSON serializer/deserializer for a safe subset of SymPy expressions
# ABOUTME: Provides a versioned, cross-SymPy-compatible AST format for JAFF

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Dict, List, Mapping, Tuple

import sympy

try:
    from sympy.core.symbol import Str as _SympyStr
except Exception:  # pragma: no cover
    _SympyStr = None

try:
    from sympy.matrices.expressions.matexpr import MatrixElement as _MatrixElement
except Exception:  # pragma: no cover
    _MatrixElement = None

try:
    from sympy.functions.elementary.piecewise import ExprCondPair as _ExprCondPair
except Exception:  # pragma: no cover
    _ExprCondPair = None


SCHEMA_VERSION = 2


class SympyJsonError(ValueError):
    pass


def dumps(
    expr: sympy.Basic,
    *,
    indent: int = 2,
    sort_keys: bool = True,
    compact: bool = True,
    include_assumptions: bool = True,
) -> str:
    payload = {
        "format": "jaff.sympy_json",
        "schema_version": SCHEMA_VERSION,
        "sympy_version": sympy.__version__,
        "expr": to_jsonable(
            expr, compact=compact, include_assumptions=include_assumptions
        ),
    }
    return json.dumps(payload, indent=indent, sort_keys=sort_keys)


def loads(s: str) -> sympy.Basic:
    payload = json.loads(s)
    if not isinstance(payload, dict) or payload.get("format") != "jaff.sympy_json":
        raise SympyJsonError("Not a jaff.sympy_json payload")
    version = payload.get("schema_version")
    if version != SCHEMA_VERSION:
        raise SympyJsonError(f"Unsupported schema_version={version!r}")
    return from_jsonable(payload.get("expr"))


def to_jsonable(
    expr: sympy.Basic, *, compact: bool = True, include_assumptions: bool = True
) -> Any:
    if not isinstance(expr, sympy.Basic):
        raise TypeError(f"Expected sympy.Basic, got {type(expr)!r}")
    if compact:
        return _EncoderCompact(include_assumptions=include_assumptions).encode(expr)
    return _Encoder(include_assumptions=include_assumptions).encode(expr)


def from_jsonable(obj: Any) -> sympy.Basic:
    if not isinstance(obj, (list, int, float)):
        raise SympyJsonError(f"Expected list/number node, got {type(obj)!r}")
    return _DecoderCompact().decode(obj)


@dataclass(frozen=True)
class _SymbolKey:
    name: str
    assumptions: Tuple[Tuple[str, bool], ...]


@dataclass(frozen=True)
class _MatrixSymbolKey:
    name: str
    rows: Any
    cols: Any


class _Encoder:
    def __init__(self, *, include_assumptions: bool) -> None:
        self._include_assumptions = include_assumptions

    def encode(self, expr: sympy.Basic) -> Dict[str, Any]:
        if expr is sympy.true:
            return {"type": "BooleanTrue"}
        if expr is sympy.false:
            return {"type": "BooleanFalse"}

        if isinstance(expr, sympy.Symbol):
            payload = {"type": "Symbol", "name": expr.name}
            if self._include_assumptions:
                payload["assumptions"] = _encode_assumptions(expr)
            return payload

        if isinstance(expr, sympy.Integer):
            return {"type": "Integer", "value": int(expr)}

        if isinstance(expr, sympy.Rational) and not isinstance(expr, sympy.Integer):
            return {"type": "Rational", "p": int(expr.p), "q": int(expr.q)}

        if isinstance(expr, sympy.Float):
            return {
                "type": "Float",
                "value": _encode_float_17(expr),
                "prec": int(expr._prec),
            }

        if _SympyStr is not None and isinstance(expr, _SympyStr):
            return {"type": "Str", "value": str(expr)}

        if isinstance(expr, sympy.MatrixSymbol):
            rows, cols = expr.shape
            return {
                "type": "MatrixSymbol",
                "name": expr.name,
                "rows": self.encode(sympy.Integer(rows))
                if isinstance(rows, int)
                else self.encode(rows),
                "cols": self.encode(sympy.Integer(cols))
                if isinstance(cols, int)
                else self.encode(cols),
            }

        if _MatrixElement is not None and isinstance(expr, _MatrixElement):
            return {
                "type": "MatrixElement",
                "base": self.encode(expr.parent),
                "i": self.encode(expr.i),
                "j": self.encode(expr.j),
            }

        if _ExprCondPair is not None and isinstance(expr, _ExprCondPair):
            return {
                "type": "ExprCondPair",
                "expr": self.encode(expr.expr),
                "cond": self.encode(expr.cond),
            }

        if isinstance(expr, sympy.StrictLessThan):
            return {
                "type": "StrictLessThan",
                "lhs": self.encode(expr.lhs),
                "rhs": self.encode(expr.rhs),
            }

        if isinstance(expr, sympy.StrictGreaterThan):
            return {
                "type": "StrictGreaterThan",
                "lhs": self.encode(expr.lhs),
                "rhs": self.encode(expr.rhs),
            }

        if isinstance(expr, sympy.Piecewise):
            pairs = []
            for pair in expr.args:
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError("Unexpected Piecewise arg type")
                pairs.append(self.encode(pair))
            return {"type": "Piecewise", "pairs": pairs}

        if isinstance(expr, sympy.Pow):
            base, exp = expr.args
            return {"type": "Pow", "base": self.encode(base), "exp": self.encode(exp)}

        if isinstance(expr, sympy.Add):
            args = [self.encode(a) for a in expr.args]
            return {"type": "Add", "args": args}

        if isinstance(expr, sympy.Mul):
            args = [self.encode(a) for a in expr.args]
            return {"type": "Mul", "args": args}

        func = expr.func
        if func is sympy.exp:
            return {"type": "exp", "args": [self.encode(expr.args[0])]}
        if func is sympy.log:
            return {"type": "log", "args": [self.encode(a) for a in expr.args]}
        if func is sympy.Max:
            return {"type": "Max", "args": [self.encode(a) for a in expr.args]}
        if func is sympy.Min:
            return {"type": "Min", "args": [self.encode(a) for a in expr.args]}

        raise SympyJsonError(f"Unsupported SymPy node: {type(expr).__name__}")


class _EncoderCompact:
    def __init__(self, *, include_assumptions: bool) -> None:
        self._include_assumptions = include_assumptions

    def encode(self, expr: sympy.Basic) -> List[Any]:
        if expr is sympy.true:
            return ["T"]
        if expr is sympy.false:
            return ["F"]

        if isinstance(expr, sympy.Symbol):
            assumptions = _encode_assumptions(expr) if self._include_assumptions else {}
            if assumptions:
                return ["S", expr.name, assumptions]
            return ["S", expr.name]

        if isinstance(expr, sympy.Integer):
            return ["I", int(expr)]

        if isinstance(expr, sympy.Rational) and not isinstance(expr, sympy.Integer):
            return ["Q", int(expr.p), int(expr.q)]

        if isinstance(expr, sympy.Float):
            return _encode_float_17(expr)

        if _SympyStr is not None and isinstance(expr, _SympyStr):
            return ["Str", str(expr)]

        if isinstance(expr, sympy.MatrixSymbol):
            rows, cols = expr.shape
            return [
                "MS",
                expr.name,
                self.encode(sympy.Integer(rows))
                if isinstance(rows, int)
                else self.encode(rows),
                self.encode(sympy.Integer(cols))
                if isinstance(cols, int)
                else self.encode(cols),
            ]

        if _MatrixElement is not None and isinstance(expr, _MatrixElement):
            return [
                "ME",
                self.encode(expr.parent),
                self.encode(expr.i),
                self.encode(expr.j),
            ]

        if _ExprCondPair is not None and isinstance(expr, _ExprCondPair):
            return ["ECP", self.encode(expr.expr), self.encode(expr.cond)]

        if isinstance(expr, sympy.StrictLessThan):
            return ["LT", self.encode(expr.lhs), self.encode(expr.rhs)]

        if isinstance(expr, sympy.StrictGreaterThan):
            return ["GT", self.encode(expr.lhs), self.encode(expr.rhs)]

        if isinstance(expr, sympy.Piecewise):
            pairs = []
            for pair in expr.args:
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError("Unexpected Piecewise arg type")
                pairs.append(self.encode(pair))
            return ["PW", pairs]

        if isinstance(expr, sympy.Pow):
            base, exp = expr.args
            return ["Pow", self.encode(base), self.encode(exp)]

        if isinstance(expr, sympy.Add):
            args = [self.encode(a) for a in expr.args]
            return ["Add", args]

        if isinstance(expr, sympy.Mul):
            args = [self.encode(a) for a in expr.args]
            return ["Mul", args]

        func = expr.func
        if func is sympy.exp:
            return ["exp", self.encode(expr.args[0])]
        if func is sympy.log:
            return ["log", [self.encode(a) for a in expr.args]]
        if func is sympy.Max:
            return ["Max", [self.encode(a) for a in expr.args]]
        if func is sympy.Min:
            return ["Min", [self.encode(a) for a in expr.args]]

        raise SympyJsonError(f"Unsupported SymPy node: {type(expr).__name__}")


class _Decoder:
    def __init__(self) -> None:
        self._symbol_cache: Dict[_SymbolKey, sympy.Symbol] = {}
        self._matrix_symbol_cache: Dict[_MatrixSymbolKey, sympy.MatrixSymbol] = {}

    def decode(self, obj: Any) -> sympy.Basic:
        if not isinstance(obj, dict):
            raise SympyJsonError(f"Expected dict node, got {type(obj)!r}")
        t = obj.get("type")
        if not isinstance(t, str):
            raise SympyJsonError("Missing/invalid node type")

        if t == "BooleanTrue":
            return sympy.true
        if t == "BooleanFalse":
            return sympy.false

        if t == "Symbol":
            name = obj.get("name")
            if not isinstance(name, str):
                raise SympyJsonError("Symbol.name must be a string")
            assumptions = obj.get("assumptions") or {}
            if not isinstance(assumptions, dict):
                raise SympyJsonError("Symbol.assumptions must be a dict")
            cleaned = _decode_assumptions(assumptions)
            key = _SymbolKey(name=name, assumptions=tuple(sorted(cleaned.items())))
            sym = self._symbol_cache.get(key)
            if sym is None:
                sym = sympy.Symbol(name, **cleaned)
                self._symbol_cache[key] = sym
            return sym

        if t == "Integer":
            value = obj.get("value")
            if not isinstance(value, int):
                raise SympyJsonError("Integer.value must be an int")
            return sympy.Integer(value)

        if t == "Rational":
            p = obj.get("p")
            q = obj.get("q")
            if not isinstance(p, int) or not isinstance(q, int):
                raise SympyJsonError("Rational.p and Rational.q must be ints")
            return sympy.Rational(p, q)

        if t == "Float":
            prec = obj.get("prec")
            value = obj.get("value")
            if not isinstance(prec, int):
                raise SympyJsonError("Float.prec must be int")
            if not isinstance(value, (str, int, float)):
                raise SympyJsonError("Float.value must be str or number")
            return sympy.Float(value, prec)

        if t == "Str":
            value = obj.get("value")
            if not isinstance(value, str):
                raise SympyJsonError("Str.value must be a string")
            if _SympyStr is None:
                raise SympyJsonError("Str node unsupported in this SymPy build")
            return _SympyStr(value)

        if t == "MatrixSymbol":
            name = obj.get("name")
            if not isinstance(name, str):
                raise SympyJsonError("MatrixSymbol.name must be a string")
            rows = self.decode(obj.get("rows"))
            cols = self.decode(obj.get("cols"))
            key = _MatrixSymbolKey(name=name, rows=rows, cols=cols)
            msym = self._matrix_symbol_cache.get(key)
            if msym is None:
                msym = sympy.MatrixSymbol(name, rows, cols)
                self._matrix_symbol_cache[key] = msym
            return msym

        if t == "MatrixElement":
            base = self.decode(obj.get("base"))
            i = self.decode(obj.get("i"))
            j = self.decode(obj.get("j"))
            if _MatrixElement is None:
                raise SympyJsonError("MatrixElement node unsupported in this SymPy build")
            return _MatrixElement(base, i, j)

        if t == "ExprCondPair":
            expr = self.decode(obj.get("expr"))
            cond = self.decode(obj.get("cond"))
            if _ExprCondPair is None:
                raise SympyJsonError("ExprCondPair node unsupported in this SymPy build")
            return _ExprCondPair(expr, cond)

        if t == "StrictLessThan":
            lhs = self.decode(obj.get("lhs"))
            rhs = self.decode(obj.get("rhs"))
            return sympy.StrictLessThan(lhs, rhs)

        if t == "StrictGreaterThan":
            lhs = self.decode(obj.get("lhs"))
            rhs = self.decode(obj.get("rhs"))
            return sympy.StrictGreaterThan(lhs, rhs)

        if t == "Piecewise":
            pairs_obj = obj.get("pairs")
            if not isinstance(pairs_obj, list):
                raise SympyJsonError("Piecewise.pairs must be a list")
            pairs = []
            for p in pairs_obj:
                pair = self.decode(p)
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError(
                        "Piecewise.pairs must contain ExprCondPair nodes"
                    )
                pairs.append((pair.expr, pair.cond))
            return sympy.Piecewise(*pairs, evaluate=False)

        if t == "Pow":
            base = self.decode(obj.get("base"))
            exp = self.decode(obj.get("exp"))
            return sympy.Pow(base, exp, evaluate=False)

        if t == "Add":
            args = _decode_args_list(obj.get("args"))
            return sympy.Add(*[self.decode(a) for a in args], evaluate=False)

        if t == "Mul":
            args = _decode_args_list(obj.get("args"))
            return sympy.Mul(*[self.decode(a) for a in args], evaluate=False)

        if t == "exp":
            args = _decode_args_list(obj.get("args"))
            if len(args) != 1:
                raise SympyJsonError("exp expects 1 arg")
            return sympy.exp(self.decode(args[0]))

        if t == "log":
            args = _decode_args_list(obj.get("args"))
            if len(args) not in (1, 2):
                raise SympyJsonError("log expects 1 or 2 args")
            return sympy.log(*[self.decode(a) for a in args])

        if t == "Max":
            args = _decode_args_list(obj.get("args"))
            return sympy.Max(*[self.decode(a) for a in args], evaluate=False)

        if t == "Min":
            args = _decode_args_list(obj.get("args"))
            return sympy.Min(*[self.decode(a) for a in args], evaluate=False)

        raise SympyJsonError(f"Unsupported node type: {t!r}")


class _DecoderCompact:
    def __init__(self) -> None:
        self._symbol_cache: Dict[_SymbolKey, sympy.Symbol] = {}
        self._matrix_symbol_cache: Dict[_MatrixSymbolKey, sympy.MatrixSymbol] = {}

    def decode(self, obj: Any) -> sympy.Basic:
        if isinstance(obj, (int, float)):
            return sympy.Float(obj, 53)
        if not isinstance(obj, list) or not obj:
            raise SympyJsonError(f"Expected list node, got {type(obj)!r}")
        t = obj[0]
        if not isinstance(t, str):
            raise SympyJsonError("Missing/invalid node type")

        if t == "T":
            return sympy.true
        if t == "F":
            return sympy.false

        if t == "S":
            if len(obj) < 2 or not isinstance(obj[1], str):
                raise SympyJsonError("Symbol name missing/invalid")
            name = obj[1]
            assumptions = {}
            if len(obj) >= 3:
                if not isinstance(obj[2], dict):
                    raise SympyJsonError("Symbol assumptions must be a dict")
                assumptions = _decode_assumptions(obj[2])
            key = _SymbolKey(name=name, assumptions=tuple(sorted(assumptions.items())))
            sym = self._symbol_cache.get(key)
            if sym is None:
                sym = sympy.Symbol(name, **assumptions)
                self._symbol_cache[key] = sym
            return sym

        if t == "I":
            if len(obj) != 2 or not isinstance(obj[1], int):
                raise SympyJsonError("Integer value missing/invalid")
            return sympy.Integer(obj[1])

        if t == "Q":
            if (
                len(obj) != 3
                or not isinstance(obj[1], int)
                or not isinstance(obj[2], int)
            ):
                raise SympyJsonError("Rational values missing/invalid")
            return sympy.Rational(obj[1], obj[2])

        if t == "Flt":
            if len(obj) < 3:
                raise SympyJsonError("Float value/precision missing")
            value = obj[1]
            prec = obj[2]
            if not isinstance(value, str):
                raise SympyJsonError("Float.value must be str")
            if not isinstance(prec, int):
                raise SympyJsonError("Float.prec must be int")
            return sympy.Float(value, prec)

        if t == "Str":
            if len(obj) != 2 or not isinstance(obj[1], str):
                raise SympyJsonError("Str value missing/invalid")
            if _SympyStr is None:
                raise SympyJsonError("Str node unsupported in this SymPy build")
            return _SympyStr(obj[1])

        if t == "MS":
            if len(obj) != 4 or not isinstance(obj[1], str):
                raise SympyJsonError("MatrixSymbol name/shape missing/invalid")
            name = obj[1]
            rows = self.decode(obj[2])
            cols = self.decode(obj[3])
            key = _MatrixSymbolKey(name=name, rows=rows, cols=cols)
            msym = self._matrix_symbol_cache.get(key)
            if msym is None:
                msym = sympy.MatrixSymbol(name, rows, cols)
                self._matrix_symbol_cache[key] = msym
            return msym

        if t == "ME":
            if len(obj) != 4:
                raise SympyJsonError("MatrixElement payload missing/invalid")
            base = self.decode(obj[1])
            i = self.decode(obj[2])
            j = self.decode(obj[3])
            if _MatrixElement is None:
                raise SympyJsonError("MatrixElement node unsupported in this SymPy build")
            return _MatrixElement(base, i, j)

        if t == "ECP":
            if len(obj) != 3:
                raise SympyJsonError("ExprCondPair payload missing/invalid")
            expr = self.decode(obj[1])
            cond = self.decode(obj[2])
            if _ExprCondPair is None:
                raise SympyJsonError("ExprCondPair node unsupported in this SymPy build")
            return _ExprCondPair(expr, cond)

        if t == "LT":
            if len(obj) != 3:
                raise SympyJsonError("StrictLessThan payload missing/invalid")
            return sympy.StrictLessThan(self.decode(obj[1]), self.decode(obj[2]))

        if t == "GT":
            if len(obj) != 3:
                raise SympyJsonError("StrictGreaterThan payload missing/invalid")
            return sympy.StrictGreaterThan(self.decode(obj[1]), self.decode(obj[2]))

        if t == "PW":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("Piecewise pairs missing/invalid")
            pairs = []
            for p in obj[1]:
                pair = self.decode(p)
                if _ExprCondPair is None or not isinstance(pair, _ExprCondPair):
                    raise SympyJsonError(
                        "Piecewise pairs must contain ExprCondPair nodes"
                    )
                pairs.append((pair.expr, pair.cond))
            return sympy.Piecewise(*pairs, evaluate=False)

        if t == "Pow":
            if len(obj) != 3:
                raise SympyJsonError("Pow payload missing/invalid")
            return sympy.Pow(self.decode(obj[1]), self.decode(obj[2]), evaluate=False)

        if t == "Add":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("Add args missing/invalid")
            return sympy.Add(*[self.decode(a) for a in obj[1]], evaluate=False)

        if t == "Mul":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("Mul args missing/invalid")
            return sympy.Mul(*[self.decode(a) for a in obj[1]], evaluate=False)

        if t == "exp":
            if len(obj) != 2:
                raise SympyJsonError("exp expects 1 arg")
            return sympy.exp(self.decode(obj[1]))

        if t == "log":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("log args missing/invalid")
            if len(obj[1]) not in (1, 2):
                raise SympyJsonError("log expects 1 or 2 args")
            return sympy.log(*[self.decode(a) for a in obj[1]])

        if t == "Max":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("Max args missing/invalid")
            return sympy.Max(*[self.decode(a) for a in obj[1]], evaluate=False)

        if t == "Min":
            if len(obj) != 2 or not isinstance(obj[1], list):
                raise SympyJsonError("Min args missing/invalid")
            return sympy.Min(*[self.decode(a) for a in obj[1]], evaluate=False)

        raise SympyJsonError(f"Unsupported node type: {t!r}")


def _decode_args_list(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        raise SympyJsonError("args must be a list")
    for item in value:
        if not isinstance(item, dict):
            raise SympyJsonError("args must contain dict nodes")
    return value


def _encode_float_17(value: sympy.Float) -> float:
    return float(str(sympy.Float(value, 17)))


def _encode_assumptions(sym: sympy.Symbol) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for k, v in (sym.assumptions0 or {}).items():
        if isinstance(k, str) and isinstance(v, bool):
            out[k] = v
    return out


def _decode_assumptions(assumptions: Mapping[str, Any]) -> Dict[str, bool]:
    out: Dict[str, bool] = {}
    for k, v in assumptions.items():
        if isinstance(k, str) and isinstance(v, bool):
            out[k] = v
    return out
