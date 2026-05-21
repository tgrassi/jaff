#!/usr/bin/env python3
# ABOUTME: Test module to verify CSE (Common Subexpression Elimination) works in C++ code generation
# ABOUTME: Tests that common subexpressions in reaction rates are properly identified and extracted

import os
from pathlib import Path

import pytest

from jaff.codegen import Codegen
from jaff import Network


@pytest.fixture
def test_network():
    """Load the test network with common subexpressions."""
    network_file = Path(__file__).parent / "fixtures" / "test_cse.dat"
    if not network_file.exists():
        pytest.skip(f"Test network file not found: {network_file}")
    return Network(str(network_file))


@pytest.fixture
def test_codegen(test_network):
    """Create a Codegen instance for the test network."""
    return Codegen(test_network, lang="c++")


def test_cse_generates_common_subexpressions(test_codegen):
    """Test that CSE identifies and extracts common subexpressions."""
    rates_with_cse = test_codegen.get_rates_str(use_cse=True)

    # Check that common subexpressions were found
    common_subexpr_count = rates_with_cse.count("const double x")
    assert common_subexpr_count > 0, (
        "CSE should identify common subexpressions in the test network"
    )


def test_cse_reduces_redundancy(test_codegen):
    """Test that CSE reduces redundant calculations."""
    rates_no_cse = test_codegen.get_rates_str(use_cse=False)
    rates_with_cse = test_codegen.get_rates_str(use_cse=True)

    # Count occurrences of exp() calls as a proxy for redundant calculations
    exp_count_no_cse = rates_no_cse.count("exp(")
    exp_count_with_cse = rates_with_cse.count("exp(")

    # With CSE, we should have fewer exp() calls in the main rate calculations
    # (some will be in the common subexpression definitions)
    assert exp_count_with_cse <= exp_count_no_cse, (
        "CSE should reduce redundant exp() calls"
    )


def test_cse_output_structure(test_codegen):
    """Test that CSE generates properly structured C++ code."""
    rates_with_cse = test_codegen.get_rates_str(use_cse=True)

    # Check for proper C++ syntax
    assert "const double" in rates_with_cse, (
        "CSE should generate const double declarations"
    )
    assert "k[" in rates_with_cse, "Should generate rate array assignments"

    # Check that lines are properly terminated
    lines = rates_with_cse.strip().split("\n")
    for line in lines:
        if line.strip() and not line.strip().startswith("//"):
            assert line.strip().endswith(";"), (
                f"C++ statements should end with semicolon: {line}"
            )


def test_cse_vs_no_cse_consistency(test_codegen):
    """Test that both CSE and non-CSE versions generate valid C++ code."""
    rates_no_cse = test_codegen.get_rates_str(use_cse=False)
    rates_with_cse = test_codegen.get_rates_str(use_cse=True)

    # Both should generate rate assignments
    assert "k[" in rates_no_cse, "Non-CSE should generate rate assignments"
    assert "k[" in rates_with_cse, "CSE should generate rate assignments"

    # Count the number of rate assignments (should be the same)
    rate_count_no_cse = rates_no_cse.count("k[")
    rate_count_with_cse = rates_with_cse.count("k[")
    assert rate_count_no_cse == rate_count_with_cse, (
        "Both versions should generate the same number of rates"
    )


def test_cse_common_patterns(test_codegen):
    """Test that CSE identifies common patterns in the test network."""
    rates_with_cse = test_codegen.get_rates_str(use_cse=True)

    # The test network has reactions with common exp(-100/tgas) and exp(-200/tgas) terms
    # These should be extracted as common subexpressions
    lines = rates_with_cse.strip().split("\n")

    # Look for extracted temperature-dependent terms
    has_temp_dependent_cse = any(
        "tgas" in line and "const double x" in line for line in lines
    )
    assert has_temp_dependent_cse, (
        "CSE should extract temperature-dependent common subexpressions"
    )


def test_network_reactions_loaded(test_network):
    """Test that the test network loads with expected reactions."""
    assert len(test_network.reactions) > 0, "Test network should contain reactions"
    assert len(test_network.reactions) == 8, (
        "Test network should contain exactly 8 reactions"
    )
