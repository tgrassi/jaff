#!/usr/bin/env python3
# Test module to verify if jacobian works properly

from pathlib import Path
from typing import List

import pytest

from jaff.codegen import Codegen
from jaff.network import Network


@pytest.fixture
def test_network():
    """Load the test network with a fake rate expression"""

    network_file = Path(__file__).parent / "fixtures" / "test_jac.dat"
    if not network_file.exists():
        pytest.skip(f"Test network file not found: {network_file}")
    print(network_file)

    return Network(str(network_file))


@pytest.fixture
def test_codegen(test_network):
    """Create a Codegen instance for the test network."""
    return Codegen(test_network, lang="c++")


@pytest.fixture
def test_network_dedt():
    """Load the test network with a fake rate expression and an internal energy expression"""

    network_file = Path(__file__).parent / "fixtures" / "test_jac_dedt.dat"
    if not network_file.exists():
        pytest.skip(f"Test network file not found: {network_file}")
    print(network_file)

    return Network(str(network_file))


@pytest.fixture
def test_codegen_dedt(test_network_dedt):
    """Create a Codegen instance for the test network with internal energy."""
    return Codegen(test_network_dedt, lang="c++")


def test_network_reactions_loaded(test_network: Network):
    """Test that the test network loads with expected reactions."""

    assert len(test_network.reactions) > 0, "Test network should contain reactions"
    assert len(test_network.reactions) == 1, (
        "Test network should contain exactly 1 reaction"
    )


def test_rates(test_codegen: Codegen):
    "Test whether the correct rate has been loaded"

    rates = test_codegen.get_rates_str().strip().split("\n")
    rate = rates[-1].split("=")[-1].strip().rstrip(";")
    expected_rate = "nden[0]"

    assert len(rates) == 1, "Number of rates should be exactly 1"
    assert rate == expected_rate, f"Rate must be equal to {expected_rate}"


def test_ode_and_jac(test_codegen: Codegen):
    "Test generated odes and jac with precalculated expression strings"

    ode = test_codegen.get_ode_str(use_cse=False)
    jac = test_codegen.get_jacobian_str(use_cse=False)

    expected_rhs: List[str] = [
        "-std::pow(nden[0], 2)*nden[1]",
        "-std::pow(nden[0], 2)*nden[1]",
        "std::pow(nden[0], 2)*nden[1]",
    ]

    expected_jac: List[str] = [
        "-2*nden[0]*nden[1]",
        "-std::pow(nden[0], 2)",
        "-2*nden[0]*nden[1]",
        "-std::pow(nden[0], 2)",
        "2*nden[0]*nden[1]",
        "std::pow(nden[0], 2)",
    ]

    ode_comp = ode.strip().split("\n")
    jac_comp = jac.strip().split("\n")

    ode_comp = [comp.split("=")[-1].strip().strip(";") for comp in ode_comp]
    jac_comp = [comp.split("=")[-1].strip().strip(";") for comp in jac_comp]

    assert len(ode_comp) == len(expected_rhs), (
        f"Number of ode equations must be equal to {len(expected_rhs)}"
    )
    assert len(jac_comp) == len(expected_jac), (
        f"Number of jacobian components must be equal to {len(expected_jac)}"
    )

    for comp, excomp in zip(ode_comp, expected_rhs):
        assert comp == excomp, f"ODE: {comp} must be equal to {excomp}"

    for comp, excomp in zip(jac_comp, expected_jac):
        assert comp == excomp, f"Jacobian: {comp} must be equal to {excomp}"


def test_network_reactions_loaded_dedt(test_network_dedt: Network):
    """Test that the test network loads with expected reactions."""

    assert len(test_network_dedt.reactions) > 0, "Test network should contain reactions"
    assert len(test_network_dedt.reactions) == 1, (
        "Test network should contain exactly 1 reaction"
    )


def test_rates_dedt(test_codegen_dedt: Codegen):
    "Test whether the correct rate has been loaded"

    rates = test_codegen_dedt.get_rates_str().strip().split("\n")
    rate = rates[-1].split("=")[-1].strip().rstrip(";")
    expected_rate = "nden[0]"

    assert len(rates) == 1, "Number of rates should be exactly 1"
    assert rate == expected_rate, f"Rate must be equal to {expected_rate}"


def test_dedt(test_network_dedt: Network):
    "Test whether the correct internal energy rate has been loaded"

    dEdt = str(test_network_dedt.dEdt_chem)
    expected_dEdt = "nden[0, 0]**3*nden[1, 0]"

    assert dEdt == expected_dEdt, f"dEdt must be equal to {expected_dEdt}"


def test_ode_and_jac_dedt(test_codegen_dedt: Codegen):
    "Test generated odes and jac with precalculated expression strings"

    rhs = test_codegen_dedt.get_rhs_str(use_cse=False)
    jac = test_codegen_dedt.get_jacobian_str(use_cse=False, use_dedt=True)

    expected_rhs: List[str] = [
        "-std::pow(nden[0], 2)*nden[1]",
        "-std::pow(nden[0], 2)*nden[1]",
        "std::pow(nden[0], 2)*nden[1]",
        "std::pow(nden[0], 3)*nden[1]",
    ]

    expected_jac: List[str] = [
        "-2*nden[0]*nden[1]",
        "-std::pow(nden[0], 2)",
        "-2*nden[0]*nden[1]",
        "-std::pow(nden[0], 2)",
        "2*nden[0]*nden[1]",
        "std::pow(nden[0], 2)",
        "3*std::pow(nden[0], 2)*nden[1]",
        "std::pow(nden[0], 3)",
    ]

    rhs_comp = rhs.strip().split("\n")
    jac_comp = jac.strip().split("\n")

    rhs_comp = [comp.split("=")[-1].strip().strip(";") for comp in rhs_comp]
    jac_comp = [comp.split("=")[-1].strip().strip(";") for comp in jac_comp]

    assert len(rhs_comp) == len(expected_rhs), (
        f"Number of ode equations must be equal to {len(expected_rhs)}"
    )
    assert len(jac_comp) == len(expected_jac), (
        f"Number of jacobian components must be equal to {len(expected_jac)}"
    )

    for comp, excomp in zip(rhs_comp, expected_rhs):
        assert comp == excomp, f"ODE: {comp} must be equal to {excomp}"

    for comp, excomp in zip(jac_comp, expected_jac):
        assert comp == excomp, f"Jacobian: {comp} must be equal to {excomp}"
