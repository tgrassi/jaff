"""
Code generation module for chemical reaction network ODEs.

This module provides the Codegen class which generates language-specific code
for chemical reaction networks, including rate calculations, flux computations,
ODE right-hand sides, and analytical Jacobians with optional common subexpression
elimination (CSE).

The code generator supports multiple programming languages and provides optimizations
through symbolic manipulation with SymPy. Generated code can be customized with
different array indexing styles, variable names, and formatting conventions.

Supported Languages:
    - C++ (cxx, cpp, c++)
    - C (c)
    - Fortran 90 (f90, fortran)
    - Python (py, python)
    - Rust (rust, rs)
    - Julia (julia, jl)
    - R (r)

Key Features:
    - Symbolic differentiation for analytical Jacobians
    - Common subexpression elimination (CSE) for optimization
    - Customizable array indexing (0-based or 1-based) with additional index offseting
    - Multiple bracket formats ([],(),{},<>)
    - Language-specific code generation via SymPy
    - Reaction flux and rate calculations
    - ODE right-hand side generation
    - Optional energy equation support

Example:
    >>> from jaff import Network, Codegen
    >>> net = Network("networks/react_COthin")
    >>> cg = Codegen(network=net, lang="cxx")
    >>> rates = cg.get_rates_str(idx_offset=0, rate_variable="k")
    >>> print(rates)
"""

import re
from collections.abc import Callable
from functools import cache, reduce
from itertools import product
from typing import Any, List, Set, Tuple, TypedDict, cast

import sympy as sp

from .jaff_types import IndexedList, IndexedValue
from .network import Network


class ExtrasDict(TypedDict):
    """
    Dictionary containing extra data from indexed code generation.

    Used to store auxiliary information alongside main expressions,
    for Common Subexpression Elimination (CSE) results.

    Attributes:
        cse: IndexedList of CSE temporary variable assignments
    """

    cse: IndexedList


class IndexedReturn(TypedDict):
    """
    Return type for indexed code generation methods.

    Structure returned by methods like get_indexed_rates(), get_indexed_odes(),
    etc. Contains both the main expressions and extra data (like CSE temporaries).

    Attributes:
        extras: Dictionary containing auxiliary data (CSE temporaries, etc.)
        expressions: IndexedList of main expressions (rates, ODEs, etc.)

    Example:
        >>> result = cg.get_indexed_rates(use_cse=True)
        >>> # Access CSE temporaries
        >>> for indices, expr in result["extras"]["cse"]:
        ...     print(f"cse{indices[0]} = {expr}")
        >>> # Access main rate expressions
        >>> for indices, rate in result["expressions"]:
        ...     print(f"k[{indices[0]}] = {rate}")
    """

    extras: ExtrasDict
    expressions: IndexedList


class LangModifier(TypedDict):
    """
    Type definition for language-specific code generation modifiers.

    Attributes:
        brac: Bracket style for 1D arrays (e.g., "[]" for C++, "()" for Fortran)
        assignment_op: Assignment operator (typically "=")
        line_end: Statement terminator (e.g., ";" for C++, "" for Python)
        matrix_sep: Separator for 2D array indexing (e.g., "][" for C++)
        code_gen: SymPy code generation function for the target language
        idx_offset: Array indexing offset (0 for C/C++/Python, 1 for Fortran)
        comment: Comment prefix for the language (e.g., "//" for C++)
        types: Dictionary mapping type names to language-specific declarations
        extras: Additional language-specific attributes (qualifiers, specifiers, etc.)
    """

    brac: str
    assignment_op: str
    line_end: str
    matrix_sep: str
    code_gen: Callable[..., str]
    idx_offset: int
    comment: str
    types: dict[str, str]
    extras: dict[str, Any]


class Codegen:
    """
    Multi-language code generator for chemical reaction networks.

    This class provides methods to generate optimized code for evaluating
    chemical reaction rates, fluxes, ODE right-hand sides, and analytical
    Jacobians in multiple programming languages.

    The Codegen class uses SymPy for symbolic manipulation and code generation,
    applying optimizations like common subexpression elimination (CSE) to reduce
    computational costs. Generated code can be customized for different array
    indexing conventions, variable naming, and language-specific syntax.

    Attributes:
        net (Network): Chemical reaction network object containing species and reactions
        lang (str): Internal language identifier ('cxx', 'c', 'f90', 'py', 'rust', 'julia', 'r')
        lb (str): Left bracket for 1D arrays (e.g., '[' for C++, '(' for Fortran)
        rb (str): Right bracket for 1D arrays (e.g., ']' for C++, ')' for Fortran)
        mlb (str): Left bracket for 2D arrays (matrices)
        mrb (str): Right bracket for 2D arrays (matrices)
        matrix_sep (str): Separator for 2D array indices (e.g., '][' for C++, ', ' for Python)
        assignment_op (str): Assignment operator (typically '=')
        line_end (str): Statement terminator (';' for C/C++, '' for Python/Fortran)
        code_gen (Callable): SymPy code generation function for target language
        ioff (int): Array indexing offset (0 for C/C++/Python, 1 for Fortran)
        comment (str): Comment prefix for the language (e.g., '//' for C++, '!!' for Fortran)
        types (dict[str, str]): Type declaration strings for the language
        extras (dict[str, Any]): Additional language-specific attributes (qualifiers, specifiers)
        dedt_str (str): Cached string for energy equation derivative
        ode_str (str): Cached string for ODE system
        jac_str (str): Cached string for Jacobian matrix

    Example:
        >>> from jaff import Network, Codegen
        >>> net = Network("networks/react_COthin")
        >>> cg = Codegen(network=net, lang="cxx")
        >>>
        >>> # Generate rate calculations
        >>> rates = cg.get_rates_str(idx_offset=0, rate_variable="k", use_cse=True)
        >>>
        >>> # Generate ODE system
        >>> odes = cg.get_ode_str(idx_offset=0, ode_var="f", use_cse=True)
        >>>
        >>> # Generate Jacobian matrix
        >>> jac = cg.get_jacobian_str(idx_offset=0, jac_var="J", use_cse=True)
    """

    def __init__(
        self,
        network: Network,
        lang: str = "c++",
        brac_format: str = "",
        matrix_format: str = "",
    ) -> None:
        """
        Initialize the code generator for a specific language and network.

        Sets up language-specific code generation parameters including bracket styles,
        array indexing conventions, statement terminators, and SymPy code generators.
        All generated code will use these settings consistently.

        Args:
            network (Network): Chemical reaction Network object containing species and reactions
            lang (str): Target programming language. Default: "c++"
                Options:
                    - "c++", "cpp", "cxx" → C++ (0-indexed, semicolons, '//' comments)
                    - "c" → C (0-indexed, semicolons, '//' comments)
                    - "fortran", "f90" → Fortran 90 (1-indexed, no semicolons, '!!' comments)
                    - "python", "py" → Python (0-indexed, no semicolons, '#' comments)
                    - "rust", "rs" → Rust (0-indexed, semicolons, '//' comments)
                    - "julia", "jl" → Julia (1-indexed, no semicolons, '#' comments)
                    - "r" → R (1-indexed, no semicolons, '#' comments)
            brac_format (str): Override for 1D array bracket style. Default: "" (use language default)
                Options: "()", "[]", "{}", "<>"
                Example: "[]" → array[i], "()" → array(i)
            matrix_format (str): Override for 2D array format. Default: "" (use language default)
                Options: "()", "(,)", "[]", "[,]", "{}", "{,}", "<>", "<,>"
                Example: "[]" → matrix[i][j], "(,)" → matrix(i,j)

        Example:
            >>> # C++ with default settings
            >>> cg = Codegen(network=net, lang="cxx")
            >>>
            >>> # Fortran with custom bracket format
            >>> cg = Codegen(network=net, lang="f90", brac_format="()")
            >>>
            >>> # Python with comma-separated 2D indexing
            >>> cg = Codegen(network=net, lang="py", matrix_format="[,]")
        """
        __lang_aliases = self.__get_language_aliases()
        __lang_tokens = self.get_language_tokens()
        __matrix_formats = self.__get_matrix_formats()
        __brack_formats = self.__get_bracket_formats()

        # Check if language is supported
        if lang and lang not in __lang_aliases.keys():
            raise ValueError(
                f"\n\nUnsupported language: '{lang}'"
                f"\nSupported languages: {[key for key in __lang_aliases]}\n"
            )

        # Check if 2D array format is supported
        if matrix_format and matrix_format not in __matrix_formats.keys():
            raise ValueError(
                f"\n\nUnsupported matrix format: '{matrix_format}'"
                f"\nSupported matrix formats: {[key for key in __matrix_formats]}\n"
            )

        # Check if 1D array format is supported
        if brac_format and brac_format not in __brack_formats:
            raise ValueError(
                f"\n\nUnsupported bracket format: '{brac_format}'"
                f"\nSupported bracket formats: {[key for key in __brack_formats]}\n"
            )

        # Set language
        language = __lang_aliases.get(lang, "cxx")

        # Set brackets for 1D array
        bracs: str = (
            brac_format
            if brac_format in __brack_formats
            else __lang_tokens[language]["brac"]
        )

        # Set brackets for 2D array
        mbracs: str = (
            __matrix_formats[matrix_format]["brac"]
            if matrix_format
            else __lang_tokens[language]["brac"]
        )

        # Set 2D array separator
        self.matrix_sep: str = (
            __matrix_formats[matrix_format]["sep"]
            if matrix_format
            else __lang_tokens[language]["matrix_sep"]
        )

        # Assign other required variables
        self.assignment_op: str = __lang_tokens[language]["assignment_op"]
        self.line_end: str = __lang_tokens[language]["line_end"]
        self.code_gen: Callable[..., str] = __lang_tokens[language]["code_gen"]
        self.ioff: int = __lang_tokens[language]["idx_offset"]
        self.comment: str = __lang_tokens[language]["comment"]
        self.types: dict[str, str] = __lang_tokens[language]["types"]
        self.extras: dict[str, Any] = __lang_tokens[language]["extras"]
        self.lang = language

        # Set left and right brackets for 1D and 2D arrays
        self.lb, self.rb = bracs
        self.mlb, self.mrb = mbracs

        # Set network object
        self.net: Network = network

    def get_commons(
        self,
        idx_offset: int = -1,
        idx_prefix: str = "",
        definition_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate code for common constants (species indices, counts).

        This method generates index definitions for all species in the network,
        along with the total number of species and reactions.

        Args:
            idx_offset: Starting index for species (default: -1 uses language default)
            idx_prefix: Prefix to add before species index names (e.g., "idx_")
            definition_prefix: Prefix for definitions (e.g., "const int " for C++)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated code with species indices and counts

        Example output (C++):
            const int idx_h2 = 0;
            const int idx_co = 1;
            const int nspecs = 2;
            const int nreactions = 5;
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        scommons = ""

        # Species
        for i, s in enumerate(self.net.species):
            scommons += (
                f"{definition_prefix}{idx_prefix}{s.fidx} {assign_op} {ioff + i}{lend}\n"
            )

        scommons += (
            f"{definition_prefix}nspecs {assign_op} {len(self.net.species)}{lend}\n"
        )
        scommons += (
            f"{definition_prefix}nreactions {assign_op} {len(self.net.reactions)}{lend}\n"
        )

        return scommons

    def get_indexed_rates(
        self,
        use_cse: bool = True,
        cse_var: str = "x",
    ) -> IndexedReturn:
        """
        Generate indexed rate expressions with optional CSE optimization.

        This method generates indexed rate coefficient expressions,
        optionally applying common subexpression elimination (CSE) to optimize
        repeated calculations. Returns a structured dictionary with CSE temporaries
        and final rate expressions.

        Args:
            use_cse: Whether to apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "x")

        Returns:
            IndexedReturn: Dictionary with structure:
                {
                    "extras": {
                        "cse": IndexedList of IndexedValue([cse_idx], cse_expression)
                    },
                    "expressions": IndexedList of IndexedValue([rate_idx], rate_expression)
                }

        Note:
            - String rates and photorates functions are excluded from CSE
            - Rate expressions contain language-specific code strings
            - Use get_rates_str() when you need formatted code ready to write to file
            - Use this method when you need programmatic access to individual expressions


        Example:
            >>> result = cg.get_indexed_rates(use_cse=True, cse_var="cse")
            >>> # Access CSE temporaries
            >>> for iv in result["extras"]["cse"]:
            ...     print(f"cse[{iv.indices[0]}] = {iv.value}")
            >>> # Access rate expressions
            >>> for iv in result["expressions"]:
            ...     print(f"k[{iv.indices[0]}] = {iv.value}")
        """

        # Collect all rate expressions and apply CSE if enabled
        # CSE (Common Subexpression Elimination) identifies and extracts repeated
        # subexpressions to reduce redundant computations
        out: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }
        cse_dict: dict[int, sp.Expr | str] = {}
        if use_cse:
            # Collect all rate expressions as SymPy objects, excluding strings and photorates
            for i, rea in enumerate(self.net.reactions):
                if type(rea.rate) is str:
                    continue
                if (
                    hasattr(rea.rate, "func")
                    and isinstance(rea.rate.func, type(sp.Function("f")))
                    and rea.rate.func.__name__ == "photorates"
                ):
                    continue
                cse_dict[i] = rea.rate

            if cse_dict:
                # Apply CSE to all valid expressions
                exprs = cse_dict.values()

                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(
                    exprs, optimizations="basic", symbols=cse_var
                )

                # Prune unused CSE temporaries based on actually emitted rate expressions
                replacements = self.__prune_cse(replacements, reduced_exprs)

                if replacements:
                    pattern = re.compile(r"(\d+)")
                    for var, expr in replacements:
                        match = pattern.search(str(var))
                        idx: int = int(match.group(0)) if match is not None else 0
                        expr = self.code_gen(expr, strict=False)
                        out["extras"]["cse"].append(IndexedValue([idx], expr))

                for key, expr in zip(cse_dict.keys(), reduced_exprs):
                    expr = self.code_gen(expr, strict=False)
                    cse_dict[key] = expr

        # Collect all rate expressions (CSE-optimized or original)
        for i, rea in enumerate(self.net.reactions):
            rate = cse_dict[i] if cse_dict.get(i, "") else rea.get_code(self.lang)
            out["expressions"].append(IndexedValue([i], rate))

        return out

    def get_rates_str(
        self,
        idx_offset: int = -1,
        rate_variable: str = "k",
        brac_format: str = "",
        use_cse: bool = True,
        cse_var: str = "x",
        var_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate formatted code string for reaction rate coefficient calculations.

        This method generates complete code to compute all reaction rate coefficients,
        optionally applying common subexpression elimination (CSE) to optimize
        repeated calculations. Includes variable declarations and assignments.

        Args:
            idx_offset: Starting index for rate array (default: -1 uses language default)
            rate_variable: Name of the rate array variable (default: "k")
            brac_format: Override for 1D array bracket style (default: "" uses language default)
            use_cse: Whether to apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "x")
            var_prefix: Prefix for CSE variable declarations (default: "" uses language default)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated rate calculation code

        Note:
            - String rates and photorates functions are excluded from CSE
            - CSE temporaries are declared and assigned before rate assignments
            - photorates $IDX$ placeholders are replaced with actual reaction indices
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            var_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        # Use provided bracket format or default language brackets
        lb, rb = brac_format or (self.lb, self.rb)
        # Use provided operators/terminators or language defaults
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        rates = ""

        # Get rate expressions with optional CSE optimization
        rate_expressions = self.get_indexed_rates(use_cse=use_cse, cse_var=cse_var)

        # Generate CSE temporary variable assignments first
        if use_cse:
            for idx, expression in rate_expressions["extras"]["cse"]:
                _idx = idx[0]
                rates += f"{prefix}{cse_var}{_idx} {assign_op} {expression}{lend}\n"

        # Generate main rate array assignments
        for idx, expression in rate_expressions["expressions"]:
            _idx = idx[0]
            # Replace $IDX$ placeholder in photorates with actual index
            if "$IDX$" in expression:
                expression = expression.replace("$IDX$", str(ioff + _idx))
            rates += (
                f"{rate_variable}{lb}{ioff + _idx}{rb} {assign_op} {expression}{lend}\n"
            )

        return rates

    def get_indexed_flux_expressions(
        self,
    ) -> IndexedList:
        """
        Generate indexed flux expressions for all reactions.

        This method creates IndexedValue objects representing flux calculations
        for each reaction. Fluxes are the products of rate coefficients and
        reactant concentrations: flux[i] = k[i] * product(reactants).

        Returns:
            IndexedList: List of IndexedValue([reaction_idx], flux_expression) objects.
                Each flux expression contains the template placeholder '$IDX$' for
                the reaction index and uses fidx (formatted index) for species names.
                Bracket formats are language-specific (self.lb/self.rb).
                Overrides for this may be added in the future

        Note:
            - Flux expressions use template placeholders replaced during template parsing
            - Use get_flux_expressions_str() for formatted code strings ready to write
            - IndexedList allows programmatic access to individual flux expressions
            - Generated expressions are language-independent templates

        Example:
            >>> cg = Codegen(network, lang="cxx")
            >>> fluxes = cg.get_indexed_flux_expressions()
            >>> for iv in fluxes:
            ...     print(f"Reaction {iv.indices[0]}: {iv.value}")
            Reaction 0: k[$IDX$] * y[h] * y[o]
            Reaction 1: k[$IDX$] * y[co]
        """
        out = IndexedList()
        for i, rea in enumerate(self.net.reactions):
            for rr in rea.reactants:
                flux = f"k{self.lb}$IDX${self.rb} * " + " * ".join(
                    [f"y{self.lb}{x.fidx}{self.rb}" for x in rea.reactants]
                )

            out.append(IndexedValue([i], flux))

        return out

    def get_flux_expressions_str(
        self,
        rate_var: str = "k",
        species_var: str = "y",
        idx_prefix: str = "",
        idx_offset: int = -1,
        brac_format: str = "",
        flux_var: str = "flux",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate code for reaction flux calculations.

        This method generates code to compute reaction fluxes, which are the
        products of rate coefficients and reactant concentrations.

        Args:
            rate_var: Name of the rate coefficient array (default: "k")
            species_var: Name of the species concentration array (default: "y")
            idx_prefix: Prefix for species index names (default: "")
            idx_offset: Starting index for flux array (default: -1 uses language default)
            brac_format: Override for 1D array bracket style (default: "" uses language default)
            flux_var: Name of the flux array variable (default: "flux")
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated flux calculation code

        Example output:
            flux[0] = k[0] * y[idx_h] * y[idx_o];
            flux[1] = k[1] * y[idx_co];
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        fluxes = ""

        # Generate flux expression for each reaction
        for i, rea in enumerate(self.net.reactions):
            flux = rea.get_flux_expression(
                idx=ioff + i,
                rate_variable=rate_var,
                species_variable=species_var,
                brackets=f"{self.lb}{self.rb}",
                idx_prefix=idx_prefix,
            )
            fluxes += f"{flux_var}{lb}{ioff + i}{rb} {assign_op} {flux}{lend}\n"

        return fluxes

    def get_indexed_ode_expressions(self) -> IndexedList:
        """
        Generate indexed ODE expressions from flux contributions.

        This method constructs time derivatives (dy/dt) for each species by
        summing flux contributions with appropriate signs. Reactants contribute
        negative flux terms, products contribute positive flux terms.

        Returns:
            IndexedList: List of IndexedValue([species_idx], ode_expression) objects.
                Each ODE expression is a string of flux terms like " - flux[0] + flux[1]".
                Uses language-specific bracket formats for flux array indexing.

        Algorithm:
            1. Initialize empty expression for each species
            2. For each reaction:
               - Subtract flux from all reactants: " - flux[i]"
               - Add flux to all products: " + flux[i]"
            3. Return IndexedList of (species_index, accumulated_expression) pairs

        Note:
            - Uses symbolic flux array references: flux[i]
            - Empty expressions for species not involved in any reactions
            - Flux indices are offset by self.ioff (language-dependent: 0 or 1)
            - Use get_ode_expressions_str() for formatted code strings

        Example:
            >>> cg = Codegen(network, lang="cxx")
            >>> odes = cg.get_indexed_ode_expressions()
            >>> for iv in odes:
            ...     print(f"Species {iv.indices[0]}: dy/dt = {iv.value}")
            Species 0:  - flux[0] + flux[3]
            Species 1:  - flux[1] + flux[2]
        """
        # Build ODE expressions by accumulating flux contributions
        # Each reaction contributes to derivatives of its reactants (negative)
        # and products (positive)
        ode = {specie.index: "" for specie in self.net.species}
        for i, rea in enumerate(self.net.reactions):
            # Subtract flux for each reactant
            for rr in rea.reactants:
                rrfidx = self.net.species_dict[str(rr)]
                ode[rrfidx] += f" - flux{self.lb}{i + self.ioff}{self.rb}"
            # Add flux for each product
            for pp in rea.products:
                ppfidx = self.net.species_dict[str(pp)]
                ode[ppfidx] += f" + flux{self.lb}{i + self.ioff}{self.rb}"

        out = IndexedList()
        for idx, expr in ode.items():
            out.append(IndexedValue([idx], expr))

        return out

    def get_ode_expressions_str(
        self,
        idx_offset: int = -1,
        flux_var: str = "flux",
        species_var: str = "y",
        idx_prefix: str = "",
        derivative_prefix: str = "d",
        derivative_var: str | None = None,
        brac_format: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate code for ODE right-hand side (dy/dt).

        This method generates code for the time derivatives of all species
        concentrations by summing fluxes according to reaction stoichiometry.
        Reactants contribute negative terms, products contribute positive terms.

        Args:
            idx_offset: Starting index (default: -1 uses language default)
            flux_var: Name of the flux array (default: "flux")
            species_var: Name of the species array (default: "y")
            idx_prefix: Prefix for species index names (default: "")
            derivative_prefix: Prefix for derivative variable name (default: "d")
            derivative_var: Override name for derivative array (default: None uses
                           derivative_prefix + species_var)
            brac_format: Override for 1D array bracket style (default: "" uses language default)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated ODE code

        Example output:
            dy[idx_h2] = - flux[0] + flux[3];
            dy[idx_o] = - flux[1] + flux[2];
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        derivative_var = derivative_var or f"{derivative_prefix}{species_var}"
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        lb, rb = brac_format or (self.lb, self.rb)

        # Build ODE expressions by accumulating flux contributions
        # Each reaction contributes to derivatives of its reactants (negative)
        # and products (positive)
        ode = {}
        for i, rea in enumerate(self.net.reactions):
            # Subtract flux for each reactant
            for rr in rea.reactants:
                rrfidx = idx_prefix + rr.fidx
                if rrfidx not in ode:
                    ode[rrfidx] = ""
                ode[rrfidx] += f" - {flux_var}{self.lb}{ioff + i}{self.rb}"
            # Add flux for each product
            for pp in rea.products:
                ppfidx = idx_prefix + pp.fidx
                if ppfidx not in ode:
                    ode[ppfidx] = ""
                ode[ppfidx] += f" + {flux_var}{self.lb}{ioff + i}{self.rb}"

        sode = ""
        for name, expr in ode.items():
            sode += f"{derivative_var}{lb}{name}{rb} {assign_op} {expr}{lend}\n"

        return sode

    def __gen_sdedt(self, specific_eint: bool = False, norm: int = 0) -> sp.Expr:
        """
        Generate symbolic expression for specific internal energy time derivative.

        Computes the time derivative of specific internal energy (dedt) by
        combining chemical heating/cooling and other energy sources, normalized
        by total mass density.

        Returns:
            SymPy expression for d(e)/dt where e is specific internal energy

        Formula:
            dedt = (dEdt_chem + dEdt_other) / density_total

        Notes: This will be revisited and refined
        if specific_eint is True returns specific internal energy rate,
        else returns internal energy rate
        norm: Normalization parameter if specifict_eint is True
        norm = 0, nden is specie number density
        norm = 1, nden is specie density
        """
        nspec = len(self.net.species)
        nden_matrix = sp.MatrixSymbol("nden", nspec, 1)

        # Precompute specific internal energy equation if requested
        den_tot = 1
        if specific_eint:
            if norm not in [0, 1]:
                raise ValueError(
                    f"Invalid value of normalization: {norm}\n"
                    "Supported values of norm are 0 and 1"
                )
            if norm == 0:
                den_tot = reduce(
                    lambda x, y: x + y,
                    [
                        specie.mass * nden_matrix[i, 0]
                        for i, specie in enumerate(self.net.species)
                    ],
                    0,
                )
            elif norm == 1:
                den_tot = reduce(
                    lambda x, y: x + y,
                    [nden_matrix[i, 0] for i, _ in enumerate(self.net.species)],
                    0,
                )

        return (self.net.dEdt_chem + self.net.dEdt_other) / den_tot

    def get_dedt(self, specific_eint: bool = False, norm: int = 0) -> str:
        """
        Generate code for specific internal energy time derivative.

        This method converts the symbolic specific internal energy derivative
        expression into language-specific code.

        Returns:
            String containing the generated code for dedt calculation
        """

        expr = self.code_gen(self.__gen_sdedt(specific_eint, norm), strict=False)

        return expr

    def get_indexed_odes(
        self,
        use_cse: bool = True,
        cse_var: str = "cse",
    ) -> IndexedReturn:
        """
        Generate indexed ODE expressions with optional CSE optimization.

        This method generates symbolic ODE right-hand side expressions by computing
        derivatives from reaction fluxes and applying common subexpression elimination.
        Returns a structured dictionary with CSE temporaries and ODE expressions.

        Args:
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")

        Returns:
            IndexedReturn: Dictionary with structure:
                {
                    "extras": {
                        "cse": IndexedList of IndexedValue([cse_idx], cse_expression)
                    },
                    "expressions": IndexedList of IndexedValue([species_idx], ode_expression)
                }

        Algorithm:
            1. Get symbolic ODE expressions from network (self.net.get_sodes())
            2. Substitute k[i] symbols with actual rate expressions
            3. Apply CSE if requested to extract common subexpressions
            4. Prune unused CSE temporaries
            5. Convert to language-specific code strings

        Example:
            >>> result = cg.get_indexed_odes(use_cse=True)
            >>> # CSE temporaries
            >>> for iv in result["extras"]["cse"]:
            ...     print(f"cse[{iv.indices[0]}] = {iv.value}")
            >>> # ODE expressions
            >>> for iv in result["expressions"]:
            ...     print(f"dydt[{iv.indices[0]}] = {iv.value}")
        """
        ir: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }

        subs_k = {
            sp.symbols(f"k[{i}]"): rea.rate for i, rea in enumerate(self.net.reactions)
        }

        ode_symbols = self.net.get_sodes()
        ode_symbols = [sode.xreplace(subs_k) for sode in ode_symbols]

        if use_cse:
            cse_var = sp.numbered_symbols(prefix=cse_var)
            replacements, reduced_exprs = sp.cse(ode_symbols, symbols=cse_var)

            # Build separate CSE blocks for RHS and Jacobian
            replacements = self.__prune_cse(replacements, reduced_exprs)

            # Generate ODE code with only the needed CSE assignments
            pattern = re.compile(r"(\d+)")
            for var, expr in replacements:
                match = pattern.search(str(var))
                idx: int = int(match.group(0)) if match is not None else 0
                expr = self.code_gen(expr, strict=False)
                ir["extras"]["cse"].append(IndexedValue([idx], expr))

            ode_symbols = reduced_exprs

        # Generate ODE code without CSE
        for i, expr in enumerate(ode_symbols):
            expr = self.code_gen(expr, strict=False)
            ir["expressions"].append(IndexedValue([i], expr))

        return ir

    def get_ode_str(
        self,
        idx_offset: int = 0,
        use_cse: bool = True,
        cse_var: str = "cse",
        ode_var: str = "f",
        brac_format: str = "",
        def_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate formatted code string for ODE right-hand side with CSE optimization.

        This method generates complete code for the ODE system by computing symbolic
        derivatives and applying common subexpression elimination. Results are cached
        after the first call for efficiency.

        Args:
            idx_offset: Starting index for arrays (default: 0)
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")
            ode_var: Name of ODE output array (default: "f")
            brac_format: Override for 1D array bracket style (default: "" uses language default)
            def_prefix: Prefix for variable declarations (default: "" uses language default)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated ODE code with optional CSE optimizations

        Note:
            - CSE temporaries are declared and assigned before ODE assignments
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            def_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end

        ode_code: str = ""
        ode_expressions = self.get_indexed_odes(use_cse=use_cse, cse_var=cse_var)

        if use_cse:
            for idx, expression in ode_expressions["extras"]["cse"]:
                _idx = idx[0]
                ode_code += f"{prefix}{cse_var}{_idx} {assign_op} {expression}{lend}\n"

        for idx, expression in ode_expressions["expressions"]:
            _idx = idx[0]
            ode_code += f"{ode_var}{lb}{ioff + _idx}{rb} {assign_op} {expression}{lend}\n"

        return ode_code

    def get_indexed_rhs(
        self,
        use_cse: bool = True,
        cse_var: str = "cse",
        specific_eint: bool = False,
        norm: int = 0,
        radiation: bool = False,
        rad_order: int = 0,
    ) -> IndexedReturn:
        """
        Generate indexed right-hand side expressions (ODE + energy equation).

        This method combines the ODE system with the specific internal energy
        derivative (dedt). Returns a structured dictionary with CSE temporaries
        and all RHS expressions including the energy equation.

        Args:
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")

        Returns:
            IndexedReturn: Dictionary with structure:
                {
                    "extras": {
                        "cse": IndexedList of IndexedValue([cse_idx], cse_expression)
                    },
                    "expressions": IndexedList of IndexedValue([idx], rhs_expression)
                        where idx goes from 0 to n_species (last element is dedt)
                }

        Example:
            >>> result = cg.get_indexed_rhs(use_cse=True)
            >>> n_species = len(cg.net.species)
            >>> # Last expression is dedt
            >>> dedt_expr = result["expressions"][-1]
            >>> print(
            ...     f"Energy equation at index {dedt_expr.indices[0]}: {dedt_expr.value}"
            ... )
        """
        ir: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }

        subs_k = {
            sp.symbols(f"k[{i}]"): rea.rate for i, rea in enumerate(self.net.reactions)
        }

        rhs_symbols = self.net.get_sodes()
        rhs_symbols = [sode.xreplace(subs_k) for sode in rhs_symbols]
        rhs_symbols.extend(
            [
                self.__gen_sdedt(specific_eint, norm),
                *(self.net.get_sradodes(rad_order) if radiation else []),
            ]
        )

        if use_cse:
            cse_var = sp.numbered_symbols(prefix=cse_var)
            replacements, reduced_exprs = sp.cse(rhs_symbols, symbols=cse_var)

            # Build separate CSE blocks for RHS and Jacobian
            replacements = self.__prune_cse(replacements, reduced_exprs)

            # Generate ODE code with only the needed CSE assignments
            pattern = re.compile(r"(\d+)")
            for var, expr in replacements:
                match = pattern.search(str(var))
                idx: int = int(match.group(0)) if match is not None else 0
                expr = self.code_gen(expr, strict=False)
                ir["extras"]["cse"].append(IndexedValue([idx], expr))

            rhs_symbols = reduced_exprs

        for i, expr in enumerate(rhs_symbols):
            expr = self.code_gen(expr, strict=False)
            ir["expressions"].append(IndexedValue([i], expr))

        return ir

    def get_rhs_str(
        self,
        idx_offset: int = 0,
        use_cse: bool = True,
        cse_var: str = "cse",
        ode_var: str = "f",
        brac_format: str = "",
        def_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
        specific_eint: bool = False,
        norm: int = 0,
        radiation: bool = False,
        rad_order: int = 0,
    ) -> str:
        """
        Generate formatted code string for complete RHS (ODE + energy equation).

        This method combines the ODE system with the specific internal energy
        derivative. The energy equation is appended as the last element in the
        output array.

        Args:
            idx_offset: Starting index for arrays (default: 0)
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")
            ode_var: Name of output array (default: "f")
            brac_format: Override for 1D array bracket style (default: "" uses language default)
            def_prefix: Prefix for variable declarations (default: "" uses language default)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing ODE code followed by dedt assignment
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            def_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end

        rhs_code = ""
        rhs_expressions = self.get_indexed_rhs(
            use_cse=use_cse,
            cse_var=cse_var,
            specific_eint=specific_eint,
            norm=norm,
            radiation=radiation,
            rad_order=rad_order,
        )

        if use_cse:
            for idx, expression in rhs_expressions["extras"]["cse"]:
                _idx = idx[0]
                rhs_code += f"{prefix}{cse_var}{_idx} {assign_op} {expression}{lend}\n"

        for idx, expression in rhs_expressions["expressions"]:
            _idx = idx[0]
            rhs_code += f"{ode_var}{lb}{ioff + _idx}{rb} {assign_op} {expression}{lend}\n"

        return rhs_code

    def get_indexed_radodes(
        self, order: int = 0, use_cse: bool = True, cse_var: str = "rcse"
    ):
        ir: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }
        radode_symbols = self.net.get_sradodes(order)

        if use_cse:
            cse_var = sp.numbered_symbols(prefix=cse_var)
            replacements, reduced_exprs = sp.cse(radode_symbols, symbols=cse_var)

            # Build separate CSE blocks for RHS and Jacobian
            replacements = self.__prune_cse(replacements, reduced_exprs)

            # Generate ODE code with only the needed CSE assignments
            pattern = re.compile(r"(\d+)")
            for var, expr in replacements:
                match = pattern.search(str(var))
                idx: int = int(match.group(0)) if match is not None else 0
                expr = self.code_gen(expr, strict=False)
                ir["extras"]["cse"].append(IndexedValue([idx], expr))

            radode_symbols = reduced_exprs

        for i, expr in enumerate(radode_symbols):
            expr = self.code_gen(expr, strict=False)
            ir["expressions"].append(IndexedValue([i], expr))

        return ir

    def get_radode_str(
        self,
        idx_offset: int = 0,
        use_cse: bool = True,
        cse_var: str = "rcse",
        radode_var: str = "f",
        brac_format: str = "",
        def_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
        order: int = 0,
    ) -> str:
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            def_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end

        radode_code: str = ""
        radode_expressions = self.get_indexed_radodes(order, use_cse, cse_var)

        if use_cse:
            for idx, expression in radode_expressions["extras"]["cse"]:
                _idx = idx[0]
                radode_code += f"{prefix}{cse_var}{_idx} {assign_op} {expression}{lend}\n"

        for idx, expression in radode_expressions["expressions"]:
            _idx = idx[0]
            radode_code += (
                f"{radode_var}{lb}{ioff + _idx}{rb} {assign_op} {expression}{lend}\n"
            )

        return radode_code

    def get_indexed_jacobian(
        self,
        use_dedt: bool = False,
        use_cse: bool = True,
        cse_var: str = "cse",
        specific_eint: bool = False,
        norm: int = 0,
        radiation: bool = False,
        rad_order: int = 0,
    ) -> IndexedReturn:
        """
        Generate indexed Jacobian matrix expressions with CSE optimization.

        This method uses symbolic differentiation to compute the analytical
        Jacobian matrix (∂f/∂y) for the chemical ODE system. Common subexpression
        elimination is applied to reduce redundant calculations. Returns a
        structured dictionary with CSE temporaries and Jacobian elements.

        Args:
            use_dedt: Include energy equation derivatives (default: False)
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")

        Returns:
            IndexedReturn: Dictionary with structure:
                {
                    "extras": {
                        "cse": IndexedList of IndexedValue([cse_idx], cse_expression)
                    },
                    "expressions": IndexedList of IndexedValue([i, j], jacobian_element)
                        where i, j are row/column indices for non-zero elements only
                }

        Algorithm:
            1. Create symbolic variables y_i for each species concentration
            2. Map nden[i] references in rates to y_i symbols
            3. Substitute rate expressions into ODE system
            4. Compute Jacobian matrix via symbolic differentiation
            5. Apply CSE to extract common subexpressions
            6. Prune unused CSE temporaries
            7. Generate code only for non-zero elements
            8. Replace y_i back to nden[i] in generated code

        Example:
            >>> result = cg.get_indexed_jacobian(use_cse=True)
            >>> # CSE temporaries (1D indices)
            >>> for iv in result["extras"]["cse"]:
            ...     print(f"cse[{iv.indices[0]}] = {iv.value}")
            >>> # Jacobian elements (2D indices)
            >>> for iv in result["expressions"]:
            ...     i, j = iv.indices
            ...     print(f"jac[{i}][{j}] = {iv.value}")
            >>> # Convert to nested format
            >>> nested = result["expressions"].nested()
            >>> for iv in nested:
            ...     print(f"Row {iv.indices[0]} has {len(iv.value)} non-zero elements")
        """
        if radiation and rad_order not in [0, 1, 2, 3]:
            raise ValueError("Invalid order: Supported orders are 0, 1, 2, 3")

        ir: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }
        # Create symbolic variakbles representing species concentrations for Jacobian
        # We use temporary scalar symbols y_i for robust SymPy manipulation, then
        # remap names to `nden[i]` at codegen time to match templates.
        n_species = len(self.net.species)
        n_rad_eqns = (
            2 * self.net.radiation.nbands if radiation and self.net.radiation else 0
        )
        n_ode_eqns = n_species + int(use_dedt) + n_rad_eqns

        y_syms = [sp.symbols(f"y_{i}") for i in range(n_species)]

        # Adding photon number density and flux symbols if radiation is enabled
        if radiation and self.net.radiation:
            # Placeholders for substitution
            y_syms.extend([sp.symbols("xx") for _ in range(n_rad_eqns)])

            for i in range(self.net.radiation.nbands):
                ei, fi = self.net.radiation.ordered_index(i, rad_order)
                y_syms[n_species + ei] = sp.symbols(f"ry_{i}")
                y_syms[n_species + fi] = sp.symbols(f"fy_{i}")

        # Build mapping to replace any Indexed occurrences of nden[...] in rate expressions
        # with the corresponding scalar y_i symbols.
        nden_matrix = sp.MatrixSymbol("nden", n_species, 1)
        nden_to_y = {}
        radden_to_y = {}
        radflux_to_y = {}

        for i in range(n_species):
            # Support both nden[i] and nden[Idx(i)] forms
            nden_to_y[nden_matrix[i, 0]] = y_syms[i]
            nden_to_y[nden_matrix[sp.Idx(i), 0]] = y_syms[i]

        if radiation and self.net.radiation:
            radden_matrix = sp.MatrixSymbol(
                "radeden" if self.net.radiation.energy_density else "photden",
                self.net.radiation.nbands,
                1,
            )
            radflux_matrix = sp.MatrixSymbol("rflux", self.net.radiation.nbands, 1)

            for i in range(self.net.radiation.nbands):
                ei, fi = self.net.radiation.ordered_index(i, rad_order)
                # Support both radden[i] and radden[Idx(i)] forms
                radden_to_y[radden_matrix[i, 0]] = y_syms[n_species + ei]
                radden_to_y[radden_matrix[sp.Idx(i), 0]] = y_syms[n_species + ei]
                # Support both radflux[i] and radflux[Idx(i)] forms
                radflux_to_y[radflux_matrix[i, 0]] = y_syms[n_species + fi]
                radflux_to_y[radflux_matrix[sp.Idx(i), 0]] = y_syms[n_species + fi]

        # Precompute rate expressions with nden[...] mapped to y_i
        # This substitution allows SymPy to properly differentiate rates w.r.t. species
        k_exprs = [
            rea.rate.xreplace({**nden_to_y, **radden_to_y, **radflux_to_y})
            for rea in self.net.reactions
        ]

        # Dict to replace any remaining k[i] symbols defensively before differentiating
        subs_k = {
            sp.symbols(f"k[{i}]"): k_exprs[i] for i in range(len(self.net.reactions))
        }
        ode_symbols = self.net.get_sodes()

        if use_dedt:
            ode_symbols.append(self.__gen_sdedt(specific_eint=specific_eint, norm=norm))

        if radiation:
            ode_symbols.extend(self.net.get_sradodes(order=rad_order))

        ode_symbols = [
            sode.xreplace({**nden_to_y, **radden_to_y, **radflux_to_y, **subs_k})
            for sode in ode_symbols
        ]

        # Compute the Jacobian matrix d(f)/d(y) via symbolic differentiation
        # This gives exact analytical derivatives for stiff ODE solvers
        jacobian_matrix = sp.Matrix(ode_symbols).jacobian(y_syms)

        if use_dedt:
            # Calculate internal energy derivatives and append as extra column
            dde = sp.zeros(n_ode_eqns, 1)
            dedot_dtgas = sp.diff(self.__get_sym_eos(), sp.symbols("tgas"))

            for i in range(n_ode_eqns):
                dxdot_dtgas = sp.diff(ode_symbols[i], sp.symbols("tgas"))
                dde[i, 0] = dxdot_dtgas / dedot_dtgas
            left = jacobian_matrix[:, :n_species]
            right = jacobian_matrix[:, n_species:]

            jacobian_matrix = left.row_join(dde).row_join(right)

        # Precompile regex for fast substitution
        dpattern = re.compile(r"\by_(\d+)\b")
        if radiation and self.net.radiation is not None:
            rrdpattern = re.compile(r"\bry_(\d+)\b")
            rfdpattern = re.compile(r"\bfy_(\d+)\b")

        def replace_y(match: re.Match[str], var) -> str:
            idx = int(match.group(1))
            return f"{var}{self.lb}{idx}{self.rb}"

        # Apply common subexpression elimination if requested
        # CSE significantly reduces code size and computation time for large networks
        if use_cse:
            cse_var = sp.numbered_symbols(prefix=cse_var)
            replacements, reduced_exprs = sp.cse(list(jacobian_matrix), symbols=cse_var)

            # Build separate CSE blocks for RHS and Jacobian
            replacements = self.__prune_cse(replacements, reduced_exprs)

            # Generate Jacobian code with only the needed CSE assignments
            pattern = re.compile(r"(\d+)")
            for var, expr in replacements:
                match = pattern.search(str(var))
                idx: int = int(match.group(0)) if match is not None else 0
                expr_str = self.code_gen(expr, strict=False)
                expr_str = dpattern.sub(lambda m: replace_y(m, "nden"), expr_str)

                if radiation and self.net.radiation is not None:
                    rad = self.net.radiation
                    expr_str = rrdpattern.sub(
                        lambda m: replace_y(
                            m,
                            "radeden" if rad.energy_density else "photden",
                        ),
                        expr_str,
                    )
                    expr_str = rfdpattern.sub(lambda m: replace_y(m, "rflux"), expr_str)

                ir["extras"]["cse"].append(IndexedValue([idx], expr_str))

        # Generate Jacobian code without CSE
        for i, j in product(range(n_ode_eqns), repeat=2):
            expr = reduced_exprs[i * n_ode_eqns + j] if use_cse else jacobian_matrix[i, j]

            if expr == 0:
                continue

            expr_str = self.code_gen(expr, strict=False)
            expr_str = dpattern.sub(lambda m: replace_y(m, "nden"), expr_str)

            if radiation and self.net.radiation is not None:
                rad = self.net.radiation
                expr_str = rrdpattern.sub(
                    lambda m: replace_y(
                        m,
                        "radeden" if rad.energy_density else "photden",
                    ),
                    expr_str,
                )
                expr_str = rfdpattern.sub(lambda m: replace_y(m, "rflux"), expr_str)

            ir["expressions"].append(IndexedValue([i, j], expr_str))

        return ir

    def get_jacobian_str(
        self,
        use_dedt: bool = False,
        idx_offset: int = 0,
        use_cse: bool = True,
        cse_var: str = "cse",
        jac_var: str = "J",
        matrix_format: str = "",
        var_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """
        Generate formatted code string for analytical Jacobian matrix with CSE optimization.

        This method uses symbolic differentiation to compute the analytical
        Jacobian matrix (df/dy) for the chemical ODE system. Common subexpression
        elimination is applied to reduce redundant calculations. Results are cached
        after the first call for efficiency.

        Args:
            use_dedt: Include energy equation derivatives (default: False)
            idx_offset: Starting index for arrays (default: 0)
            use_cse: Apply common subexpression elimination (default: True)
            cse_var: Prefix for CSE temporary variable names (default: "cse")
            jac_var: Name of Jacobian matrix (default: "J")
            matrix_format: Override 2D array format (default: "" uses language default)
            var_prefix: Prefix for CSE variable declarations (default: "" uses language default)
            assignment_op: Override assignment operator (default: "" uses language default)
            line_end: Override statement terminator (default: "" uses language default)

        Returns:
            String containing the generated Jacobian code with CSE optimizations
        """
        # Set overrides
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        prefix = (
            var_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )

        __matrix_formats = self.__get_matrix_formats()
        if matrix_format and matrix_format not in __matrix_formats.keys():
            raise ValueError(
                f"\n\nUnsupported matrix format: '{matrix_format}'"
                f"\nSupported matrix formats: {[key for key in __matrix_formats]}\n"
            )

        mlb, mrb = (
            (self.mlb, self.mrb)
            if not matrix_format
            else (
                __matrix_formats[matrix_format]["brac"][0],
                __matrix_formats[matrix_format]["brac"][1],
            )
        )
        matrix_sep: str = (
            __matrix_formats[matrix_format]["sep"] if matrix_format else self.matrix_sep
        )
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end

        jac_expressions = self.get_indexed_jacobian(
            cse_var=cse_var, use_cse=use_cse, use_dedt=use_dedt
        )

        jac_code: str = ""

        if use_cse:
            for idx, expr in jac_expressions["extras"]["cse"]:
                _idx = idx[0]
                jac_code += f"{prefix}{cse_var}{_idx} {assign_op} {expr}{lend}\n"

        # Generate Jacobian code without CSE
        for [i, j], expr in jac_expressions["expressions"]:
            jac_code += f"{jac_var}{mlb}{ioff + i}{matrix_sep}{ioff + j}{mrb} {assign_op} {expr}{lend}\n"

        return jac_code

    @staticmethod
    def __prune_cse(
        replacements: List[Tuple[sp.Symbol, sp.Expr]], expressions: List[sp.Expr]
    ) -> List[Tuple[sp.Symbol, sp.Expr]]:
        """
        Prune unused CSE (common subexpression elimination) temporaries.

        This method performs transitive dependency analysis to identify which
        CSE temporary variables are actually used by the target expressions,
        removing unused temporaries that would waste memory and computation.

        Args:
            replacements: List of (symbol, expression) pairs from SymPy's CSE
            expressions: Target expressions that use the CSE symbols

        Returns:
            Filtered list of (symbol, expression) pairs containing only used CSE temps

        Algorithm:
            1. Build dependency map of CSE symbols
            2. Start with symbols directly used in target expressions
            3. Recursively add dependencies via depth-first search
            4. Return only the transitively required CSE replacements
        """
        if not replacements:
            return []

        dep_map = dict(replacements)
        cse_syms = set(dep_map.keys())

        used: set = set()

        # Depth-first search to find all transitively used CSE symbols
        # This ensures we keep CSE temps that are dependencies of dependencies
        def dfs(sym: sp.Symbol) -> None:
            """Recursively mark symbol and its dependencies as used."""
            if sym in used:
                return
            used.add(sym)

            expr = dep_map.get(sym)
            if expr is None:
                return

            for dep in cast(Set[sp.Symbol], expr.free_symbols & cse_syms):
                dfs(dep)

        for expr in expressions:
            for sym in cast(Set[sp.Symbol], expr.free_symbols & cse_syms):
                dfs(sym)

        return [(var, dep_map[var]) for var, _ in replacements if var in used]

    @staticmethod
    @cache
    def __get_sym_eos(gamma: float = 1.6666666666667) -> sp.Expr:
        """
        Get symbolic equation of state for ideal gas specific internal energy.

        Computes the symbolic expression for specific internal energy using
        the ideal gas relation e = c_v * T, where c_v is the specific heat
        capacity at constant volume given by c_v = R / (gamma - 1).

        Args:
            gamma: Adiabatic index (heat capacity ratio). Default: 5/3 for monoatomic gas

        Returns:
            SymPy expression for specific internal energy as a function of tgas

        Formula:
            e = R / (gamma - 1) * tgas
        """

        from scipy.constants import R

        _R = R * 1e7  # cgs unit
        tgas = sp.symbols("tgas")

        return _R / (gamma - 1) * tgas

    @staticmethod
    @cache
    def __get_language_aliases() -> dict[str, str]:
        """
        Get mapping of language name aliases to canonical identifiers.

        Returns:
            Dictionary mapping various language names/aliases to internal IDs
        """
        # Supported language inputs and their canonical names
        aliases: dict[str, str] = {
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

        return aliases

    @staticmethod
    @cache
    def get_language_tokens() -> dict[str, LangModifier]:
        """
        Get language-specific code generation parameters.

        Returns:
            Dictionary mapping language IDs to their LangModifier configurations

        Languages:
            - cxx: C++ (0-indexed, semicolons, const/static qualifiers)
            - c: C (0-indexed, semicolons, const/static qualifiers)
            - f90: Fortran 90 (1-indexed, no semicolons, save qualifier)
            - py: Python (0-indexed, no semicolons, no type declarations)
            - rust: Rust (0-indexed, semicolons, const/let bindings)
            - julia: Julia (1-indexed, no semicolons, const qualifier)
            - r: R (1-indexed, no semicolons, no type declarations)

        Note:
            Rust, Julia, and R support require SymPy >= 1.7 for rust_code,
            julia_code, and rcode functions respectively.
        """
        # Language-specific modifiers: syntax, indexing, code generation
        tokens: dict[str, LangModifier] = {
            # c++
            "cxx": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.cxxcode,
                "idx_offset": 0,
                "comment": "//",
                "types": {
                    "int": "int ",
                    "float": "float ",
                    "double": "double ",
                    "bool": "bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "static ",
                },
            },
            # c
            "c": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.ccode,
                "idx_offset": 0,
                "comment": "//",
                "types": {
                    "int": "int ",
                    "float": "float ",
                    "double": "double ",
                    "bool": "_Bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "static ",
                },
            },
            # fortran
            "fortran": {
                "brac": "()",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ", ",
                "code_gen": sp.fcode,
                "idx_offset": 1,
                "comment": "!",
                "types": {},
                "extras": {
                    "class_specifier": "save ",
                },
            },
            # python
            "python": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": "][",
                "code_gen": sp.pycode,
                "idx_offset": 0,
                "comment": "#",
                "types": {},
                "extras": {},
            },
            # rust
            "rust": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": ";",
                "matrix_sep": "][",
                "code_gen": sp.rust_code,
                "idx_offset": 0,
                "comment": "//",
                "types": {
                    "int": "i32 ",
                    "float": "f32 ",
                    "double": "f64 ",
                    "bool": "bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "",
                },
            },
            # julia
            "julia": {
                "brac": "[]",
                "assignment_op": "=",
                "line_end": "",
                "matrix_sep": ", ",
                "code_gen": sp.julia_code,
                "idx_offset": 1,
                "comment": "#",
                "types": {
                    "int": "Int64 ",
                    "float": "Float32 ",
                    "double": "Float64 ",
                    "bool": "Bool ",
                },
                "extras": {
                    "type_qualifier": "const ",
                    "class_specifier": "",
                },
            },
            # r
            "r": {
                "brac": "[]",
                "assignment_op": "<-",
                "line_end": "",
                "matrix_sep": ", ",
                "code_gen": sp.rcode,
                "idx_offset": 1,
                "comment": "#",
                "types": {},
                "extras": {},
            },
        }

        return tokens

    @staticmethod
    @cache
    def __get_matrix_formats() -> dict[str, dict[str, str]]:
        """
        Get available 2D array indexing formats.

        Returns:
            Dictionary of format names to bracket/separator specifications

        Formats:
            - "()", "[,]", etc.: Different combinations of bracket styles
            - Each specifies both the bracket characters and index separator
        """
        # 2D array formats for different matrix indexing styles
        # Allows flexibility for various APIs (e.g., A[i][j] vs A(i,j))
        formats: dict[str, dict[str, str]] = {
            "()": {"brac": "()", "sep": ")("},
            "()()": {"brac": "()", "sep": ")("},
            "(,)": {"brac": "()", "sep": ", "},
            "[]": {"brac": "[]", "sep": "]["},
            "[][]": {"brac": "[]", "sep": "]["},
            "[,]": {"brac": "[]", "sep": ", "},
            "{}": {"brac": "{}", "sep": "}{"},
            "{}{}": {"brac": "{}", "sep": "}{"},
            "{,}": {"brac": "{}", "sep": ", "},
            "<>": {"brac": "<>", "sep": "><"},
            "<><>": {"brac": "<>", "sep": "><"},
            "<,>": {"brac": "<>", "sep": ", "},
        }
        return formats

    @staticmethod
    @cache
    def __get_bracket_formats() -> list[str]:
        """
        Get available 1D array bracket formats.

        Returns:
            List of valid bracket pair strings for 1D array indexing
        """
        formats: list[str] = ["()", "{}", "[]", "<>"]

        return formats
