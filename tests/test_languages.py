#!/usr/bin/env python3
"""
Test module for language support

Tests code generation for languages to ensure
proper syntax, indexing, and code generation.
"""

from pathlib import Path

import pytest

from jaff.codegen import Codegen
from jaff import Network


@pytest.fixture
def simple_network():
    """Load a simple test network for language testing."""
    network_file = Path(__file__).parent / "fixtures" / "test_jac.dat"
    if not network_file.exists():
        pytest.skip(f"Test network file not found: {network_file}")

    return Network(str(network_file))


class TestCLanguage:
    """Test C code generation."""

    def test_c_initialization(self, simple_network):
        """Test that C codegen initializes correctly."""
        cg = Codegen(simple_network, lang="c")
        assert cg.lang == "c"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 0  # C uses 0-based indexing
        assert cg.line_end == ";"
        assert cg.comment == "//"

    def test_c_types(self, simple_network):
        """Test C type declarations."""
        cg = Codegen(simple_network, lang="c")
        assert cg.types.get("int") == "int "
        assert cg.types.get("float") == "float "
        assert cg.types.get("double") == "double "
        assert cg.types.get("bool") == "_Bool "

    def test_c_rate_generation(self, simple_network):
        """Test basic rate code generation for C."""
        cg = Codegen(simple_network, lang="c")
        rates = cg.get_rates_str(idx_offset=0, rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert rates.count(";") > 0  # Semicolons present
        assert "=" in rates  # Assignment operator

    def test_c_matrix_separator(self, simple_network):
        """Test that C uses ][ for matrix indexing."""
        cg = Codegen(simple_network, lang="c")
        assert cg.matrix_sep == "]["


class TestCxxLanguage:
    """Test C++ code generation."""

    def test_cxx_initialization(self, simple_network):
        """Test that C++ codegen initializes correctly."""
        cg = Codegen(simple_network, lang="cxx")
        assert cg.lang == "cxx"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 0  # C++ uses 0-based indexing
        assert cg.line_end == ";"
        assert cg.comment == "//"

    def test_cxx_aliases(self, simple_network):
        """Test that 'c++' and 'cpp' aliases work for C++."""
        cg_cpp = Codegen(simple_network, lang="cpp")
        assert cg_cpp.lang == "cxx"

        cg_cplus = Codegen(simple_network, lang="c++")
        assert cg_cplus.lang == "cxx"

    def test_cxx_types(self, simple_network):
        """Test C++ type declarations."""
        cg = Codegen(simple_network, lang="cxx")
        assert cg.types.get("int") == "int "
        assert cg.types.get("float") == "float "
        assert cg.types.get("double") == "double "
        assert cg.types.get("bool") == "bool "

    def test_cxx_rate_generation(self, simple_network):
        """Test basic rate code generation for C++."""
        cg = Codegen(simple_network, lang="cxx")
        rates = cg.get_rates_str(idx_offset=0, rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert rates.count(";") > 0  # Semicolons present
        assert "=" in rates  # Assignment operator

    def test_cxx_matrix_separator(self, simple_network):
        """Test that C++ uses ][ for matrix indexing."""
        cg = Codegen(simple_network, lang="cxx")
        assert cg.matrix_sep == "]["


class TestFortranLanguage:
    """Test Fortran code generation."""

    def test_fortran_initialization(self, simple_network):
        """Test that Fortran codegen initializes correctly."""
        cg = Codegen(simple_network, lang="fortran")
        assert cg.lang == "fortran"
        assert cg.lb == "("
        assert cg.rb == ")"
        assert cg.ioff == 1  # Fortran uses 1-based indexing
        assert cg.line_end == ""  # No semicolons
        assert cg.comment == "!"

    def test_fortran_alias(self, simple_network):
        """Test that 'f90' alias works for Fortran."""
        cg = Codegen(simple_network, lang="f90")
        assert cg.lang == "fortran"

    def test_fortran_types(self, simple_network):
        """Test Fortran type declarations."""
        cg = Codegen(simple_network, lang="fortran")
        assert cg.types.get("int") is None
        assert cg.types.get("float") is None
        assert cg.types.get("double") is None
        assert cg.types.get("bool") is None

    def test_fortran_indexing(self, simple_network):
        """Test that Fortran uses 1-based indexing."""
        cg = Codegen(simple_network, lang="fortran")
        rates = cg.get_rates_str(idx_offset=-1, rate_variable="k", use_cse=False)

        # Should use default 1-based indexing
        assert "k(1)" in rates or "(1)" in rates
        assert "k(0)" not in rates  # Should not have 0-based indexing

    def test_fortran_rate_generation(self, simple_network):
        """Test basic rate code generation for Fortran."""
        cg = Codegen(simple_network, lang="fortran")
        rates = cg.get_rates_str(rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k(" in rates  # Parenthesis indexing
        assert "=" in rates  # Assignment operator

    def test_fortran_matrix_separator(self, simple_network):
        """Test that Fortran uses comma for matrix indexing."""
        cg = Codegen(simple_network, lang="fortran")
        assert cg.matrix_sep == ", "


class TestPythonLanguage:
    """Test Python code generation."""

    def test_python_initialization(self, simple_network):
        """Test that Python codegen initializes correctly."""
        cg = Codegen(simple_network, lang="python")
        assert cg.lang == "python"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 0  # Python uses 0-based indexing
        assert cg.line_end == ""  # No semicolons
        assert cg.comment == "#"

    def test_python_alias(self, simple_network):
        """Test that 'py' alias works for Python."""
        cg = Codegen(simple_network, lang="py")
        assert cg.lang == "python"

    def test_python_types(self, simple_network):
        """Test Python type declarations."""
        cg = Codegen(simple_network, lang="python")
        # Python uses empty string for types (dynamically typed)
        assert cg.types.get("int") is None
        assert cg.types.get("float") is None
        assert cg.types.get("double") is None
        assert cg.types.get("bool") is None

    def test_python_rate_generation(self, simple_network):
        """Test basic rate code generation for Python."""
        cg = Codegen(simple_network, lang="python")
        rates = cg.get_rates_str(idx_offset=0, rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert "=" in rates  # Assignment operator

    def test_python_matrix_separator(self, simple_network):
        """Test that Python uses ][ for matrix indexing."""
        cg = Codegen(simple_network, lang="python")
        assert cg.matrix_sep == "]["


class TestRustLanguage:
    """Test Rust code generation."""

    def test_rust_initialization(self, simple_network):
        """Test that Rust codegen initializes correctly."""
        cg = Codegen(simple_network, lang="rust")
        assert cg.lang == "rust"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 0  # Rust uses 0-based indexing
        assert cg.line_end == ";"
        assert cg.comment == "//"

    def test_rust_alias(self, simple_network):
        """Test that 'rs' alias works for Rust."""
        cg = Codegen(simple_network, lang="rs")
        assert cg.lang == "rust"

    def test_rust_types(self, simple_network):
        """Test Rust type declarations."""
        cg = Codegen(simple_network, lang="rust")
        assert cg.types.get("int") == "i32 "
        assert cg.types.get("float") == "f32 "
        assert cg.types.get("double") == "f64 "
        assert cg.types.get("bool") == "bool "

    def test_rust_rate_generation(self, simple_network):
        """Test basic rate code generation for Rust."""
        cg = Codegen(simple_network, lang="rust")
        rates = cg.get_rates_str(idx_offset=0, rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert rates.count(";") > 0  # Semicolons present
        assert "=" in rates  # Assignment operator


class TestJuliaLanguage:
    """Test Julia code generation."""

    def test_julia_initialization(self, simple_network):
        """Test that Julia codegen initializes correctly."""
        cg = Codegen(simple_network, lang="julia")
        assert cg.lang == "julia"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 1  # Julia uses 1-based indexing
        assert cg.line_end == ""  # No semicolons
        assert cg.comment == "#"

    def test_julia_alias(self, simple_network):
        """Test that 'jl' alias works for Julia."""
        cg = Codegen(simple_network, lang="jl")
        assert cg.lang == "julia"

    def test_julia_types(self, simple_network):
        """Test Julia type declarations."""
        cg = Codegen(simple_network, lang="julia")
        assert cg.types.get("int") == "Int64 "
        assert cg.types.get("float") == "Float32 "
        assert cg.types.get("double") == "Float64 "
        assert cg.types.get("bool") == "Bool "

    def test_julia_indexing(self, simple_network):
        """Test that Julia uses 1-based indexing."""
        cg = Codegen(simple_network, lang="julia")
        rates = cg.get_rates_str(idx_offset=-1, rate_variable="k", use_cse=False)

        # Should use default 1-based indexing
        assert "k[1]" in rates or "[1]" in rates
        assert "k[0]" not in rates  # Should not have 0-based indexing

    def test_julia_rate_generation(self, simple_network):
        """Test basic rate code generation for Julia."""
        cg = Codegen(simple_network, lang="julia")
        rates = cg.get_rates_str(rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert "=" in rates  # Assignment operator
        # Julia doesn't require semicolons


class TestRLanguage:
    """Test R code generation."""

    def test_r_initialization(self, simple_network):
        """Test that R codegen initializes correctly."""
        cg = Codegen(simple_network, lang="r")
        assert cg.lang == "r"
        assert cg.lb == "["
        assert cg.rb == "]"
        assert cg.ioff == 1  # R uses 1-based indexing
        assert cg.line_end == ""  # No semicolons
        assert cg.comment == "#"

    def test_r_assignment_operator(self, simple_network):
        """Test that R uses <- assignment operator."""
        cg = Codegen(simple_network, lang="r")
        assert cg.assignment_op == "<-"

    def test_r_indexing(self, simple_network):
        """Test that R uses 1-based indexing."""
        cg = Codegen(simple_network, lang="r")
        rates = cg.get_rates_str(idx_offset=-1, rate_variable="k", use_cse=False)

        # Should use default 1-based indexing
        assert "k[1]" in rates or "[1]" in rates
        assert "k[0]" not in rates  # Should not have 0-based indexing

    def test_r_rate_generation(self, simple_network):
        """Test basic rate code generation for R."""
        cg = Codegen(simple_network, lang="r")
        rates = cg.get_rates_str(rate_variable="k", use_cse=False)

        # Check basic syntax elements
        assert "k[" in rates  # Array indexing
        assert "<-" in rates  # R assignment operator


class TestLanguageComparison:
    """Test differences between languages."""

    def test_indexing_comparison(self, simple_network):
        """Compare indexing offsets across languages."""
        # 0-based languages
        for lang in ["cxx", "c", "python", "rust"]:
            cg = Codegen(simple_network, lang=lang)
            assert cg.ioff == 0, f"{lang} should use 0-based indexing"

        # 1-based languages
        for lang in ["fortran", "julia", "r"]:
            cg = Codegen(simple_network, lang=lang)
            assert cg.ioff == 1, f"{lang} should use 1-based indexing"

    def test_semicolon_usage(self, simple_network):
        """Compare semicolon usage across languages."""
        # Languages with semicolons
        for lang in ["cxx", "c", "rust"]:
            cg = Codegen(simple_network, lang=lang)
            assert cg.line_end == ";", f"{lang} should use semicolons"

        # Languages without semicolons
        for lang in ["python", "fortran", "julia", "r"]:
            cg = Codegen(simple_network, lang=lang)
            assert cg.line_end == "", f"{lang} should not require semicolons"

    def test_matrix_separator(self, simple_network):
        """Compare matrix indexing across languages."""
        cg_cxx = Codegen(simple_network, lang="cxx")
        cg_julia = Codegen(simple_network, lang="julia")
        cg_r = Codegen(simple_network, lang="r")

        # C++ uses ][
        assert cg_cxx.matrix_sep == "]["
        # Julia and R use comma separation
        assert cg_julia.matrix_sep == ", "
        assert cg_r.matrix_sep == ", "


def test_all_languages_aliases(simple_network):
    """Test that all language aliases work correctly."""
    aliases = {
        "c++": "cxx",
        "cpp": "cxx",
        "cxx": "cxx",
        "c": "c",
        "fortran": "fortran",
        "f90": "fortran",
        "python": "python",
        "py": "python",
        "rust": "rust",
        "rs": "rust",
        "julia": "julia",
        "jl": "julia",
        "r": "r",
    }

    for alias, canonical in aliases.items():
        cg = Codegen(simple_network, lang=alias)
        assert cg.lang == canonical, f"Alias '{alias}' should map to '{canonical}'"


@pytest.mark.parametrize("lang", ["c", "cxx", "fortran", "python", "rust", "julia", "r"])
def test_flux_generation(simple_network, lang):
    """Test flux generation for all supported languages."""
    cg = Codegen(simple_network, lang=lang)
    fluxes = cg.get_flux_expressions_str(flux_var="flux")

    # Basic checks
    assert len(fluxes) > 0
    if lang == "fortran":
        assert "flux(" in fluxes
    else:
        assert "flux[" in fluxes


@pytest.mark.parametrize("lang", ["c", "cxx", "fortran", "python", "rust", "julia", "r"])
def test_ode_generation(simple_network, lang):
    """Test ODE generation for all supported languages."""
    cg = Codegen(simple_network, lang=lang)
    odes = cg.get_ode_str(ode_var="f", use_cse=False)
    assert len(odes) > 0
