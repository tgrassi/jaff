# ABOUTME: Unit tests for Network JSON serialization
# ABOUTME: Ensures Network.to_jaff/from_jaff round-trip preserves reactions

import gzip
import json
import os
import sys
import tempfile
from unittest.mock import patch

import pytest
import sympy

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from jaff.network import Network


def test_network_json_roundtrip_sample_kida_valid():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    path = os.path.join(fixtures_dir, "sample_kida_valid.dat")

    with patch("builtins.print"):
        net = Network(path)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jaff", delete=False) as f:
        json_path = f.name

    try:
        net.to_jaff(json_path)

        # `.jaff` files are gzip-compressed by default.
        with open(json_path, "rb") as fb:
            assert fb.read(2) == b"\x1f\x8b"

        with gzip.open(json_path, "rt", encoding="utf-8") as f:
            payload = json.load(f)
        rate_symbols = payload.get("rate_symbols")
        assert isinstance(rate_symbols, list)
        rate_symbols_by_name = {
            item.get("name"): item.get("assumptions")
            for item in rate_symbols
            if isinstance(item, dict)
        }
        expected_symbols = {
            s
            for r in net.reactions
            if isinstance(r.rate, sympy.Basic)
            for s in r.rate.free_symbols
        }
        assert set(rate_symbols_by_name.keys()) == {s.name for s in expected_symbols}
        for sym in expected_symbols:
            expected_assumptions = {
                k: v
                for k, v in (sym.assumptions0 or {}).items()
                if isinstance(k, str) and isinstance(v, bool)
            }
            assert rate_symbols_by_name.get(sym.name) == expected_assumptions

        def _assert_no_symbol_assumptions(node):
            if isinstance(node, list):
                if node and node[0] == "S" and len(node) > 2:
                    raise AssertionError(
                        "Symbol node should not include assumptions in rate expressions"
                    )
                for item in node:
                    _assert_no_symbol_assumptions(item)
            elif isinstance(node, dict):
                if node.get("type") == "Symbol" and "assumptions" in node:
                    raise AssertionError(
                        "Symbol node should not include assumptions in rate expressions"
                    )
                for value in node.values():
                    _assert_no_symbol_assumptions(value)
            elif isinstance(node, (list, tuple)):
                for item in node:
                    _assert_no_symbol_assumptions(item)

        for rj in payload.get("reactions") or []:
            rate_node = rj.get("rate")
            if isinstance(rate_node, dict) and rate_node.get("kind") == "string":
                continue
            if rate_node is not None:
                _assert_no_symbol_assumptions(rate_node)

        net2 = Network(json_path)

        assert net2.label == net.label
        assert len(net2.species) == len(net.species)
        assert len(net2.reactions) == len(net.reactions)

        for r1, r2 in zip(net.reactions, net2.reactions):
            assert r2.get_verbatim() == r1.get_verbatim()
            assert r2.tmin == r1.tmin
            assert r2.tmax == r1.tmax

            if isinstance(r1.rate, str):
                assert r2.rate == r1.rate
            else:
                assert isinstance(r2.rate, sympy.Basic)
                diff = sympy.simplify(r2.rate - r1.rate)
                symbols = sorted(diff.free_symbols, key=lambda s: s.name)
                if not symbols:
                    diff_val = abs(float(diff.evalf()))
                    r1_symbols = getattr(r1.rate, "free_symbols", set())
                    if r1_symbols:
                        ref_val = abs(
                            float(sympy.N(r1.rate.subs({s: 1.0 for s in r1_symbols})))
                        )
                    else:
                        ref_val = abs(float(sympy.N(r1.rate)))
                    assert diff_val <= 1e-15 * max(1.0, ref_val)
                else:
                    for offset in (1.1, 10.1):
                        subs = {s: float(offset + i) for i, s in enumerate(symbols)}
                        val1 = float(sympy.N(r1.rate.subs(subs)))
                        val2 = float(sympy.N(r2.rate.subs(subs)))
                        assert abs(val2 - val1) <= 1e-12 * max(1.0, abs(val1))

            if isinstance(r1.dE, sympy.Basic) or isinstance(r2.dE, sympy.Basic):
                assert sympy.simplify(r2.dE - r1.dE) == 0
            else:
                assert r2.dE == r1.dE

        # Backward compatibility: legacy uncompressed `.jaff` should still load.
        with gzip.open(json_path, "rt", encoding="utf-8") as f:
            payload = f.read()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jaff", delete=False) as f:
            legacy_path = f.name
            f.write(payload)

        try:
            net3 = Network(legacy_path)
            assert len(net3.species) == len(net.species)
            assert len(net3.reactions) == len(net.reactions)
        finally:
            os.unlink(legacy_path)
    finally:
        os.unlink(json_path)
