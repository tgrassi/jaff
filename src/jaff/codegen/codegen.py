"""Multi-language code generator for astrochemical network ODEs.

This module exposes the :class:`Codegen` class which transforms a parsed
:class:`~jaff.core.network.Network` into assignment statements for reaction
rates, chemical-flux expressions, ODE right-hand sides (RHS), and analytical
Jacobians in any of the seven supported target languages.

Supported target languages
--------------------------
C++ / CXX, C, Fortran 90, Python, Rust, Julia, R.

Typical workflow
----------------
1. Parse the network with :class:`~jaff.core.network.Network`.
2. Instantiate :class:`Codegen` for the desired language.
3. Call the ``get_*_str()`` helpers to obtain formatted code strings.
4. Insert those strings into template files via the
   :class:`~jaff.codegen.preprocessor.Preprocessor`.

The module also defines :class:`LangModifier`, a :class:`~typing.TypedDict`
that captures all syntax differences between languages (bracket style,
assignment operator, line terminator, index offset, etc.).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import cache, reduce
from itertools import product
from typing import TYPE_CHECKING, Any, List, Set, Tuple, TypedDict, cast

import sympy as sp

from ..io._logger import JaffLogger, jaff_progress
from ..types import IndexedList, IndexedValue
from ._typing import IndexedReturn

if TYPE_CHECKING:
    import logging

    from ..core.network import Network


class LangModifier(TypedDict):
    """Language-specific syntax and code-generation parameters.

    Each field captures a syntax convention that differs between target
    languages.  Instances are produced by :meth:`Codegen.get_language_tokens`
    and stored on the :class:`Codegen` instance during construction.

    Attributes
    ----------
    brac : str
        Two-character string containing the left and right brackets used for
        1-D array indexing, e.g. ``"[]"`` for C/C++/Python or ``"()"`` for
        Fortran.
    assignment_op : str
        Assignment operator string, e.g. ``"="`` or ``"<-"`` (R).
    line_end : str
        Statement terminator appended after each assignment, e.g. ``";"``
        for C/C++ or ``""`` for Python/Fortran.
    matrix_sep : str
        Separator between the row and column indices in 2-D array access,
        e.g. ``"]["`` for C-style ``J[i][j]`` or ``", "`` for Julia/Fortran
        ``J[i, j]``.
    code_gen : Callable[..., str]
        SymPy printer function used to serialise expressions into target-
        language syntax, e.g. :func:`sympy.cxxcode` or :func:`sympy.fcode`.
    idx_offset : int
        Base index added to all array subscripts.  ``0`` for 0-based
        languages (C, Python, Rust), ``1`` for 1-based languages (Fortran,
        Julia, R).
    comment : str
        Single-line comment prefix, e.g. ``"//"`` or ``"!"`` or ``"#"``.
    types : dict[str, str]
        Mapping from generic type names (``"int"``, ``"float"``,
        ``"double"``, ``"bool"``) to their language-specific spellings,
        e.g. ``{"double": "f64 "}`` for Rust.  Empty for dynamically typed
        languages (Python, R, Fortran).
    extras : dict[str, Any]
        Language-specific miscellaneous tokens such as ``"type_qualifier"``
        (``"const "`` in C/C++) or ``"class_specifier"`` (``"static "`` in
        C/C++, ``"save "`` in Fortran).
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
    """Generate rates, fluxes, ODEs, and Jacobians from a Network in multiple languages.

    :class:`Codegen` is the central code-generation engine for JAFF.  Given a
    parsed :class:`~jaff.core.network.Network` it can produce assignment
    statements for:

    * **Reaction rates** — ``k[i] = <rate_expr>``
    * **Flux expressions** — ``flux[i] = k[i] * y[r1] * y[r2]``
    * **ODE right-hand sides** — ``dy[i]/dt = sum(±flux[j])``
    * **Analytical Jacobian** — ``J[i, j] = ∂f_i/∂y_j``
    * **Energy derivative** — ``dE/dt`` (optional, with EOS coupling)
    * **Radiation ODEs** — moment-equations for radiation fields (optional)

    All ``get_*_str()`` methods accept formatting overrides (bracket style,
    assignment operator, line terminator, index offset) so the same
    :class:`Codegen` object can be used to produce code for slightly
    non-standard target conventions without re-instantiation.

    Common subexpression elimination (CSE) is performed via
    :func:`sympy.cse` when ``use_cse=True`` (the default for most methods).
    CSE temporaries are emitted before the main expressions and named with a
    numeric suffix, e.g. ``cse0``, ``cse1``, …

    Parameters
    ----------
    network : Network
        Parsed chemical reaction network.
    lang : str, optional
        Target language alias.  Accepted values: ``"c++"``, ``"cpp"``,
        ``"cxx"``, ``"c"``, ``"fortran"``, ``"f90"``, ``"python"``,
        ``"py"``, ``"rust"``, ``"rs"``, ``"julia"``, ``"jl"``, ``"r"``.
        Default is ``"c++"``.
    brac_format : str, optional
        Override the 1-D array bracket style.  One of ``"()"``, ``"[]"``,
        ``"{}"`` or ``"<>"``.  When empty the language default is used.
    matrix_format : str, optional
        Override the 2-D array bracket/separator style.  Accepted values:
        ``"()"``, ``"(,)"``, ``"[]"``, ``"[,]"``, ``"{}"`` ``"{,}"``,
        ``"<>"``, ``"<,>"``, and their doubled equivalents (``"()()"``,
        etc.).  When empty the language default is used.

    Raises
    ------
    ValueError
        If *lang*, *brac_format* or *matrix_format* is not in the set of
        supported values.
    """

    def __init__(
        self,
        network: Network,
        lang: str = "c++",
        brac_format: str = "",
        matrix_format: str = "",
    ) -> None:
        # Resolve static lookup tables once — they are @cache'd so the cost
        # is paid only on the very first instantiation.
        __lang_aliases = self.__get_language_aliases()
        __lang_tokens = self.get_language_tokens()
        __matrix_formats = self.__get_matrix_formats()
        __brack_formats = self.__get_bracket_formats()

        # ------------------------------------------------------------------ #
        # Input validation                                                     #
        # ------------------------------------------------------------------ #

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

        # ------------------------------------------------------------------ #
        # Language token resolution                                            #
        # ------------------------------------------------------------------ #

        # Normalise alias (e.g. "c++" -> "cxx", "py" -> "python")
        language = __lang_aliases.get(lang, "cxx")

        # Resolve 1-D bracket pair (lb, rb) — caller override takes priority
        bracs: str = (
            brac_format
            if brac_format in __brack_formats
            else __lang_tokens[language]["brac"]
        )

        # Resolve 2-D bracket pair used for matrix/Jacobian indexing
        mbracs: str = (
            __matrix_formats[matrix_format]["brac"]
            if matrix_format
            else __lang_tokens[language]["brac"]
        )

        # Separator between row and column indices in 2-D access (e.g. "][" or ", ")
        self.matrix_sep: str = (
            __matrix_formats[matrix_format]["sep"]
            if matrix_format
            else __lang_tokens[language]["matrix_sep"]
        )

        # Store language-specific syntax tokens as instance attributes so
        # every get_*_str() method can access them without extra lookup.
        self.assignment_op: str = __lang_tokens[language]["assignment_op"]
        self.line_end: str = __lang_tokens[language]["line_end"]
        self.code_gen: Callable[..., str] = __lang_tokens[language]["code_gen"]
        self.ioff: int = __lang_tokens[language]["idx_offset"]
        self.comment: str = __lang_tokens[language]["comment"]
        self.types: dict[str, str] = __lang_tokens[language]["types"]
        self.extras: dict[str, Any] = __lang_tokens[language]["extras"]
        self.lang = language

        # Unpack bracket pairs for convenient use in f-strings below
        self.lb, self.rb = bracs
        self.mlb, self.mrb = mbracs

        self.net: Network = network
        self.logger: logging.Logger = JaffLogger().get_logger()

    def get_commons(
        self,
        idx_offset: int = -1,
        idx_prefix: str = "",
        definition_prefix: str = "",
        assignment_op: str = "",
        line_end: str = "",
    ) -> str:
        """Generate species index definitions and network-size constants.

        Produces one assignment per species that maps its formatted index name
        (``fidx``) to its position in the density array, followed by the total
        species count (``nspecs``) and reaction count (``nreactions``).

        Example output for C++ with two species H and H2 (``fidx`` names are
        lower-cased)::

            const int idx_h  = 0;
            const int idx_h2 = 1;
            const int nspecs = 2;
            const int nreactions = 5;

        Parameters
        ----------
        idx_offset : int, optional
            Base index added to each species position.  ``-1`` uses the
            language default stored in ``self.ioff``.
        idx_prefix : str, optional
            String prepended to each species index name, e.g. ``"idx_"``.
        definition_prefix : str, optional
            String prepended to each definition line, e.g. ``"const int "``
            for C/C++.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses ``self.assignment_op``.
        line_end : str, optional
            Line terminator override.  Empty string uses ``self.line_end``.

        Returns
        -------
        str
            Multi-line string of index definitions followed by the size
            constants ``nspecs`` and ``nreactions``.
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        scommons = ""

        # One definition per species: <prefix><prefix_idx><fidx> = <offset + i>
        for i, s in enumerate(self.net.species):
            scommons += (
                f"{definition_prefix}{idx_prefix}{s.fidx} {assign_op} {ioff + i}{lend}\n"
            )

        # Append network-size constants used by solver loops
        scommons += (
            f"{definition_prefix}nspecs {assign_op} {self.net.species.count}{lend}\n"
        )
        scommons += f"{definition_prefix}nreactions {assign_op} {self.net.reactions.count}{lend}\n"

        return scommons

    def get_indexed_rates(
        self,
        use_cse: bool = True,
        cse_var: str = "x",
    ) -> IndexedReturn:
        """Return rate-coefficient expressions as an :class:`~jaff.types.IndexedReturn`.

        Applies SymPy CSE across all symbolic rates to minimise repeated
        sub-expression evaluation in the generated code.  Two categories of
        rates are **excluded** from CSE because they cannot be simplified
        symbolically:

        * Rates stored as raw strings (e.g. user-supplied C code snippets).
        * ``photorates($IDX$, ...)`` calls (photochemistry; the ``$IDX$``
          placeholder cannot be absorbed into a shared sub-expression).

        Use :meth:`get_rates_str` for a formatted string ready to paste into
        a source file.

        Parameters
        ----------
        use_cse : bool, optional
            Enable SymPy common subexpression elimination.  Default ``True``.
        cse_var : str, optional
            Prefix for auto-generated CSE temporary variable names.
            Default ``"x"``, yielding ``x0``, ``x1``, …

        Returns
        -------
        IndexedReturn
            Dictionary with two keys:

            * ``"extras"["cse"]`` — :class:`~jaff.types.IndexedList` of
              ``(idx, expr_str)`` pairs for CSE temporaries.
            * ``"expressions"`` — :class:`~jaff.types.IndexedList` of
              ``(reaction_idx, rate_str)`` pairs for the final rate of each
              reaction (possibly referencing CSE temporaries).
        """
        out: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }
        # Maps reaction index -> symbolic rate for reactions eligible for CSE.
        # String rates and photorates() calls are excluded (see docstring).
        cse_dict: dict[int, sp.Basic | str] = {}
        if use_cse:
            for i, rea in enumerate(self.net.reactions):
                # Skip raw-string rates — they are already valid target-language code
                if type(rea.rate) is str:
                    continue
                # Skip photorates() calls — the $IDX$ placeholder prevents CSE
                if (
                    hasattr(rea.rate, "func")
                    and isinstance(rea.rate.func, type(sp.Function("f")))
                    and rea.rate.func.__name__ == "photorates"
                ):
                    continue
                cse_dict[i] = rea.rate

            if cse_dict:
                exprs = cse_dict.values()

                # Create a numbered symbol generator for CSE temp names
                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(
                    exprs, optimizations="basic", symbols=cse_var
                )

                # Drop CSE temporaries not referenced by any reduced expression
                replacements = self.__prune_cse(replacements, reduced_exprs)

                if replacements:
                    # Extract numeric suffix from the temp symbol name (e.g. "x3" -> 3)
                    pattern = re.compile(r"(\d+)")
                    for var, expr in replacements:
                        match = pattern.search(str(var))
                        idx: int = int(match.group(0)) if match is not None else 0
                        expr = self.code_gen(
                            expr, strict=False, allow_unknown_functions=True
                        )
                        out["extras"]["cse"].append(IndexedValue([idx], expr))

                # Overwrite the original symbolic rates with their CSE-reduced forms
                for key, expr in zip(cse_dict.keys(), reduced_exprs):
                    expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
                    cse_dict[key] = expr

        # Build the final expression list for all reactions.
        # Reactions absent from cse_dict (string/photorates) fall back to
        # their get_code() representation, which handles $IDX$ substitution
        # and string-rate passthrough.
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
        """Generate rate-coefficient assignment code as a multi-line string.

        Delegates to :meth:`get_indexed_rates` to obtain (optionally CSE-
        reduced) rate expressions, then formats them as::

            x0 = <cse_expr>;         // CSE temporaries (if any)
            k[0] = x0 * exp(-alpha); // reaction 0 rate
            k[1] = photorates(1, …); // reaction 1 (photorates with index substituted)
            …

        The ``$IDX$`` placeholder in any ``photorates(...)`` expression is
        replaced here with the concrete integer reaction index (adjusted by
        *idx_offset*) so the emitted code compiles without further processing.

        Parameters
        ----------
        idx_offset : int, optional
            Base index for array subscripts.  ``-1`` uses the language default.
        rate_variable : str, optional
            Name of the rate array.  Default ``"k"``.
        brac_format : str, optional
            Override 1-D bracket style (``"[]"``, ``"()"``, …).  Empty string
            uses the language default.
        use_cse : bool, optional
            Enable CSE.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"x"``.
        var_prefix : str, optional
            Type declaration prefix for CSE temporaries, e.g. ``"const double "``.
            When empty, the language-default type qualifier and ``double`` type
            are used.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.

        Returns
        -------
        str
            Multi-line string of rate-coefficient assignments, including any
            CSE temporary definitions.
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        # Construct the type prefix for CSE temporary declarations
        prefix = (
            var_prefix
            or f"{self.extras.get('type_qualifier', '')}{self.types.get('double', '')}"
        )
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        rates = ""

        rate_expressions = self.get_indexed_rates(use_cse=use_cse, cse_var=cse_var)

        # Emit CSE temporary definitions first so the main rate lines can
        # reference them without forward-declaration issues.
        if use_cse:
            for idx, expression in rate_expressions["extras"]["cse"]:
                _idx = idx[0]
                rates += f"{prefix}{cse_var}{_idx} {assign_op} {expression}{lend}\n"

        for idx, expression in rate_expressions["expressions"]:
            _idx = idx[0]
            # Replace the $IDX$ placeholder in photorates expressions with
            # the actual zero/one-based reaction index.
            if "$IDX$" in expression:
                expression = expression.replace("$IDX$", str(ioff + _idx))
            rates += (
                f"{rate_variable}{lb}{ioff + _idx}{rb} {assign_op} {expression}{lend}\n"
            )

        return rates

    def get_indexed_flux_expressions(
        self,
    ) -> IndexedList:
        """Return per-reaction flux expressions as an :class:`~jaff.types.IndexedList`.

        Each flux is the product of the reaction's rate coefficient and all
        reactant densities::

            flux[i] = k[$IDX$] * y[r1] * y[r2] * …

        The ``$IDX$`` placeholder is left literal here and replaced with the
        concrete reaction index when the expressions are rendered to a string
        by :meth:`get_flux_expressions_str` or
        :meth:`~jaff.codegen._template_engine.TemplateParser`.

        Returns
        -------
        IndexedList
            One entry per reaction.  Each entry is an
            :class:`~jaff.types.IndexedValue` of ``([reaction_index], flux_str)``.
        """
        out = IndexedList()
        for i, rea in enumerate(self.net.reactions):
            # Build the flux string by iterating over all reactants.
            # The loop body overwrites `flux` on each iteration so only the
            # last reactant's contribution survives — this is intentional
            # because `rea.reactants` always yields the same reactant list and
            # we need the full product expression, not individual terms.
            for rr in rea.reactants:
                flux = f"k{self.lb}$IDX${self.rb} * " + " * ".join(
                    [f"y{self.lb}{x.fidx}{self.rb}" for x in rea.reactants.core]
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
        """Generate flux-assignment code as a multi-line string.

        Produces one line per reaction of the form::

            flux[i] = k[i] * y[r1] * y[r2]

        where *r1*, *r2*, … are the formatted indices (``fidx``) of the
        reaction's reactant species.  The concrete flux expression is built by
        :meth:`~jaff.core.reaction.Reaction.get_flux_expression` on each
        :class:`~jaff.core.reaction.Reaction` object.

        Parameters
        ----------
        rate_var : str, optional
            Name of the rate-coefficient array.  Default ``"k"``.
        species_var : str, optional
            Name of the species density array.  Default ``"y"``.
        idx_prefix : str, optional
            Prefix prepended to species index names inside the expression,
            e.g. ``"idx_"`` to yield ``y[idx_H]``.
        idx_offset : int, optional
            Base index for array subscripts.  ``-1`` uses the language default.
        brac_format : str, optional
            Override 1-D bracket style.  Empty string uses the language default.
        flux_var : str, optional
            Name of the flux array.  Default ``"flux"``.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.

        Returns
        -------
        str
            Multi-line string of flux assignments, one per reaction.
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        lb, rb = brac_format or (self.lb, self.rb)
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        fluxes = ""

        for i, rea in enumerate(self.net.reactions):
            # Delegate to the Reaction object so reactant-density product
            # logic stays in one place and is language-bracket-aware.
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
        """Return per-species ODE flux-sum expressions as an :class:`~jaff.types.IndexedList`.

        Constructs the symbolic right-hand side for each species density ODE
        by collecting all fluxes that produce or consume that species::

            dn_i/dt = - flux[j1] - flux[j2] + flux[j3] + …

        Reactant species appear with a negative sign (consumption) and product
        species with a positive sign (production).

        Notes
        -----
        This method references a pre-computed ``flux`` array by name (e.g.
        ``flux[0]``, ``flux[1]``, …) rather than expanding the full rate
        expressions inline.  The flux array must therefore be populated in the
        generated code before the ODE right-hand sides are evaluated.

        Returns
        -------
        IndexedList
            One entry per species.  Each entry is an
            :class:`~jaff.types.IndexedValue` of ``([species_index], sum_str)``
            where *sum_str* is a signed sum of ``flux[j]`` terms.
        """

        with jaff_progress.indeterminate("Generating ode expressions"):
            # Initialise an empty accumulator string for every species
            ode = {specie.index: "" for specie in self.net.species}
            for i, rea in enumerate(self.net.reactions):
                # Consumption: each reactant loses density at the reaction flux rate
                for rr in rea.reactants.core:
                    ode[rr.index] += f" - flux{self.lb}{i + self.ioff}{self.rb}"
                # Production: each product gains density at the reaction flux rate
                for pp in rea.products.core:
                    ode[pp.index] += f" + flux{self.lb}{i + self.ioff}{self.rb}"

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
        """Generate ``dy/dt`` assignment code using a pre-computed flux array.

        Produces one line per species of the form::

            dy[idx_H] = -flux[0] + flux[3]
            dy[idx_H2] = +flux[0] - flux[1]

        Unlike :meth:`get_indexed_ode_expressions`, this method uses the
        species formatted-index name (``fidx``) as the subscript so the output
        integrates naturally with symbolic-index constants (e.g. ``idx_H = 0``
        defined by :meth:`get_commons`).

        Parameters
        ----------
        idx_offset : int, optional
            Base index for flux array subscripts.  ``-1`` uses the language
            default stored in ``self.ioff``.
        flux_var : str, optional
            Name of the pre-computed flux array.  Default ``"flux"``.
        species_var : str, optional
            Name of the species density array used to derive the derivative
            variable name.  Default ``"y"``.
        idx_prefix : str, optional
            Prefix prepended to each species index name, e.g. ``"idx_"``.
        derivative_prefix : str, optional
            Prefix prepended to *species_var* to form the derivative variable
            name when *derivative_var* is not given.  Default ``"d"``
            (yields ``"dy"``).
        derivative_var : str or None, optional
            Explicit name for the derivative array (overrides
            *derivative_prefix* + *species_var*).
        brac_format : str, optional
            Override 1-D bracket style.  Empty string uses the language default.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.

        Returns
        -------
        str
            Multi-line string of derivative assignments, one per active species.
        """
        ioff = idx_offset if idx_offset >= 0 else self.ioff
        # Construct the derivative variable name (e.g. "dy") unless overridden
        derivative_var = derivative_var or f"{derivative_prefix}{species_var}"
        assign_op = assignment_op or self.assignment_op
        lend = line_end or self.line_end
        lb, rb = brac_format or (self.lb, self.rb)

        # Accumulate signed flux contributions into a dict keyed by species fidx
        ode = {}
        for i, rea in enumerate(self.net.reactions):
            for rr in rea.reactants.core:
                rrfidx = idx_prefix + rr.fidx
                if rrfidx not in ode:
                    ode[rrfidx] = ""
                # Reactants are consumed: negative contribution
                ode[rrfidx] += f" - {flux_var}{self.lb}{ioff + i}{self.rb}"
            for pp in rea.products.core:
                ppfidx = idx_prefix + pp.fidx
                if ppfidx not in ode:
                    ode[ppfidx] = ""
                # Products are created: positive contribution
                ode[ppfidx] += f" + {flux_var}{self.lb}{ioff + i}{self.rb}"

        sode = ""
        for name, expr in ode.items():
            sode += f"{derivative_var}{lb}{name}{rb} {assign_op} {expr}{lend}\n"

        return sode

    def __gen_sdedt(self, specific_eint: bool = False, norm: int = 0) -> sp.Expr:
        """Return the symbolic total energy time-derivative expression.

        Computes ``(dE/dt_chem + dE/dt_other) / den_tot`` where ``den_tot``
        depends on the *specific_eint* and *norm* flags:

        * ``specific_eint=False`` → ``den_tot = 1`` (energy density rate, erg/cm³/s).
        * ``specific_eint=True, norm=0`` → ``den_tot = Σ m_i · nden[i]`` (total mass
          density in g/cm³; result is the specific internal-energy rate erg/g/s).
        * ``specific_eint=True, norm=1`` → ``den_tot = Σ nden[i]`` (total number
          density in cm⁻³; result is per-particle energy rate erg/particle/s).

        ``nden`` is treated as a SymPy :class:`~sympy.MatrixSymbol` of shape
        ``(nspec, 1)`` so that the Jacobian computation can differentiate
        through it.

        Parameters
        ----------
        specific_eint : bool, optional
            Whether to normalise by total density to obtain a *specific*
            internal-energy rate.  Default ``False``.
        norm : int, optional
            Normalisation convention when *specific_eint* is ``True``.
            ``0`` normalises by mass density; ``1`` by number density.
            Ignored when *specific_eint* is ``False``.

        Returns
        -------
        sympy.Expr
            Symbolic expression for the total energy time-derivative.

        Raises
        ------
        ValueError
            If *specific_eint* is ``True`` and *norm* is not ``0`` or ``1``.
        """
        nspec = self.net.species.count
        # nden is a symbolic column vector representing species number densities
        nden_matrix = sp.MatrixSymbol("nden", nspec, 1)

        den_tot = 1
        if specific_eint:
            if norm not in [0, 1]:
                raise ValueError(
                    f"Invalid value of normalization: {norm}\n"
                    "Supported values of norm are 0 and 1"
                )
            if norm == 0:
                # Total mass density: Σ m_i * nden[i]
                den_tot = reduce(
                    lambda x, y: x + y,
                    [
                        specie.mass * nden_matrix[i, 0]
                        for i, specie in enumerate(self.net.species)
                    ],
                    0,
                )
            elif norm == 1:
                # Total number density: Σ nden[i]
                den_tot = reduce(
                    lambda x, y: x + y,
                    [nden_matrix[i, 0] for i, _ in enumerate(self.net.species)],
                    0,
                )
        assert isinstance(self.net.dEdt_chem, sp.Expr)
        assert isinstance(self.net.dEdt_other, sp.Expr)

        return (self.net.dEdt_chem + self.net.dEdt_other) / den_tot

    def get_dedt(self, specific_eint: bool = False, norm: int = 0) -> str:
        """Return a target-language code string for the energy time-derivative.

        Calls :meth:`__gen_sdedt` to obtain the symbolic expression and then
        serialises it using the language-appropriate SymPy printer.

        Parameters
        ----------
        specific_eint : bool, optional
            Normalise by density to yield the *specific* internal-energy rate.
            Default ``False``.
        norm : int, optional
            Normalisation convention (``0`` = mass density, ``1`` = number
            density).  Used only when *specific_eint* is ``True``.

        Returns
        -------
        str
            Single-expression code string (no assignment or line terminator).
        """
        expr = self.code_gen(
            self.__gen_sdedt(specific_eint, norm),
            strict=False,
            allow_unknown_functions=True,
        )

        return expr

    def get_indexed_odes(
        self,
        use_cse: bool = True,
        cse_var: str = "cse",
    ) -> IndexedReturn:
        """Return symbolic ODE RHS expressions as an :class:`~jaff.types.IndexedReturn`.

        Builds the full per-species ``dn_i/dt`` expressions by substituting
        the reaction rate symbols ``k[i]`` with their concrete symbolic rate
        expressions from the network, then optionally applying CSE to the
        entire system at once.

        The substitution ``k[i] → rate_expr`` is performed using
        :meth:`sympy.Basic.xreplace` rather than :meth:`sympy.Basic.subs`
        for performance (xreplace does exact structural matching without
        triggering simplification).

        Parameters
        ----------
        use_cse : bool, optional
            Apply SymPy CSE across all ODE expressions.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``,
            yielding ``cse0``, ``cse1``, …

        Returns
        -------
        IndexedReturn
            Dictionary with:

            * ``"extras"["cse"]`` — CSE temporaries as
              :class:`~jaff.types.IndexedList`.
            * ``"expressions"`` — per-species ODE expressions as
              :class:`~jaff.types.IndexedList`.
        """
        with jaff_progress.indeterminate("Generating odes"):
            ir: IndexedReturn = {
                "extras": {"cse": IndexedList()},
                "expressions": IndexedList(),
            }

            # Map symbolic rate placeholders k[i] to concrete rate expressions
            subs_k = {
                sp.symbols(f"k[{i}]"): rea.rate
                for i, rea in enumerate(self.net.reactions)
            }

            # Retrieve symbolic dn_i/dt expressions and inline the rates
            ode_symbols = self.net.sodes()
            ode_symbols = [sode.xreplace(subs_k) for sode in ode_symbols]

        if use_cse:
            with jaff_progress.indeterminate("Generating cse expressions"):
                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(ode_symbols, symbols=cse_var)

                # Remove unused CSE temporaries to keep generated code lean
                replacements = self.__prune_cse(replacements, reduced_exprs)

                # Extract numeric suffix from temp name (e.g. "cse7" -> 7)
                pattern = re.compile(r"(\d+)")
                for var, expr in replacements:
                    match = pattern.search(str(var))
                    idx: int = int(match.group(0)) if match is not None else 0
                    expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
                    ir["extras"]["cse"].append(IndexedValue([idx], expr))

                # Switch to CSE-reduced forms for the main expression list
                ode_symbols = reduced_exprs

        for i, expr in enumerate(
            jaff_progress.track(ode_symbols, description="Generating ode code")
        ):
            expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
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
        """Generate ODE right-hand side assignment code as a multi-line string.

        Wraps :meth:`get_indexed_odes` and formats the result as::

            const double cse0 = …;   // CSE temporaries (if any)
            f[0] = cse0 * nden[1];   // dn_H/dt
            f[1] = …;                // dn_H2/dt
            …

        Parameters
        ----------
        idx_offset : int, optional
            Base index for species ODE array subscripts.  Default ``0``.
        use_cse : bool, optional
            Enable CSE.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``.
        ode_var : str, optional
            Name of the output ODE array.  Default ``"f"``.
        brac_format : str, optional
            Override 1-D bracket style.  Empty string uses the language default.
        def_prefix : str, optional
            Type declaration prefix for CSE temporaries.  Empty string uses the
            language-default type qualifier and ``double`` type.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.

        Returns
        -------
        str
            Multi-line string of ODE assignments, including any CSE temporaries.
        """
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

        # Emit CSE temporaries before the main ODE assignments
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
        """Return the combined ODE + energy (+ radiation) RHS as an :class:`~jaff.types.IndexedReturn`.

        Assembles the full right-hand side vector by concatenating, in order:

        1. Per-species density ODEs (``dn_i/dt`` for each species).
        2. Energy time-derivative (``dE/dt``).
        3. Radiation ODEs (optional, appended only when *radiation* is ``True``).

        CSE is applied simultaneously across the *entire* vector so that
        sub-expressions shared between the chemistry and energy/radiation
        equations are factored out together, maximising reuse.

        Parameters
        ----------
        use_cse : bool, optional
            Enable joint CSE across all RHS equations.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``.
        specific_eint : bool, optional
            Normalise the energy derivative by total density.  Default ``False``.
        norm : int, optional
            Density normalisation convention (``0`` = mass, ``1`` = number).
            Used only when *specific_eint* is ``True``.
        radiation : bool, optional
            Include radiation moment ODEs in the RHS.  Default ``False``.
        rad_order : int, optional
            Order of the radiation moment closure (``0``–``3``).  Used only
            when *radiation* is ``True``.

        Returns
        -------
        IndexedReturn
            Dictionary with:

            * ``"extras"["cse"]`` — CSE temporaries.
            * ``"expressions"`` — All RHS expressions in the order described
              above, indexed sequentially from 0.
        """
        with jaff_progress.indeterminate("Generating rhs equations"):
            ir: IndexedReturn = {
                "extras": {"cse": IndexedList()},
                "expressions": IndexedList(),
            }

            # Substitute symbolic rate placeholders with concrete expressions
            subs_k = {
                sp.symbols(f"k[{i}]"): rea.rate
                for i, rea in enumerate(self.net.reactions)
            }

            # Start with species density ODEs; inline rate expressions
            rhs_symbols = self.net.sodes()
            rhs_symbols = [sode.xreplace(subs_k) for sode in rhs_symbols]
            # Append energy derivative and (optionally) radiation ODEs
            rhs_symbols.extend(
                [
                    self.__gen_sdedt(specific_eint, norm),
                    *(self.net.sradodes(rad_order) if radiation else []),
                ]
            )

        if use_cse:
            with jaff_progress.indeterminate("Generating cse expressions"):
                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(rhs_symbols, symbols=cse_var)

                # Prune CSE temporaries unreachable from any expression
                replacements = self.__prune_cse(replacements, reduced_exprs)

                pattern = re.compile(r"(\d+)")
                for var, expr in replacements:
                    match = pattern.search(str(var))
                    idx: int = int(match.group(0)) if match is not None else 0
                    expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
                    ir["extras"]["cse"].append(IndexedValue([idx], expr))

                rhs_symbols = reduced_exprs

        for i, expr in enumerate(
            jaff_progress.track(rhs_symbols, description="Generating RHS code")
        ):
            expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
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
        """Generate the full RHS assignment code as a multi-line string.

        Wraps :meth:`get_indexed_rhs` and formats the combined species ODE,
        energy, and (optional) radiation expressions as::

            const double cse0 = …;  // CSE temporaries
            f[0] = …;               // dn_H/dt
            …
            f[N] = …;               // dE/dt
            f[N+1] = …;             // radiation ODE 0 (if radiation=True)

        Parameters
        ----------
        idx_offset : int, optional
            Base index for the output array subscripts.  Default ``0``.
        use_cse : bool, optional
            Enable joint CSE across all RHS equations.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``.
        ode_var : str, optional
            Name of the output RHS array.  Default ``"f"``.
        brac_format : str, optional
            Override 1-D bracket style.  Empty string uses the language default.
        def_prefix : str, optional
            Type declaration prefix for CSE temporaries.  Empty string uses the
            language-default type qualifier and ``double`` type.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.
        specific_eint : bool, optional
            Normalise the energy derivative by density.  Default ``False``.
        norm : int, optional
            Density normalisation convention for the energy derivative.
        radiation : bool, optional
            Include radiation moment ODEs.  Default ``False``.
        rad_order : int, optional
            Radiation moment closure order.  Default ``0``.

        Returns
        -------
        str
            Multi-line string of all RHS assignments including CSE temporaries.
        """
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

        # Emit CSE temporaries before the main assignments
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
    ) -> IndexedReturn:
        """Return radiation moment ODE expressions as an :class:`~jaff.types.IndexedReturn`.

        Retrieves the symbolic radiation moment equations from
        :meth:`~jaff.core.network.Network.sradodes` for the specified closure
        order and optionally applies CSE.

        Parameters
        ----------
        order : int, optional
            Radiation moment closure order (``0``–``3``).  Passed directly to
            :meth:`~jaff.core.network.Network.sradodes`.  Default ``0``.
        use_cse : bool, optional
            Enable CSE across the radiation ODE expressions.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"rcse"``,
            yielding ``rcse0``, ``rcse1``, …

        Returns
        -------
        IndexedReturn
            Dictionary with:

            * ``"extras"["cse"]`` — CSE temporaries.
            * ``"expressions"`` — radiation ODE expressions indexed
              sequentially from 0.
        """
        ir: IndexedReturn = {
            "extras": {"cse": IndexedList()},
            "expressions": IndexedList(),
        }
        radode_symbols = self.net.sradodes(order)

        if use_cse:
            with jaff_progress.indeterminate("Generating cse expressions"):
                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(radode_symbols, symbols=cse_var)

                # Prune unreferenced CSE temporaries to avoid dead code
                replacements = self.__prune_cse(replacements, reduced_exprs)

                # Emit only the CSE temporaries actually used by the radiation ODEs
                pattern = re.compile(r"(\d+)")
                for var, expr in replacements:
                    match = pattern.search(str(var))
                    idx: int = int(match.group(0)) if match is not None else 0
                    expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
                    ir["extras"]["cse"].append(IndexedValue([idx], expr))

                radode_symbols = reduced_exprs

        for i, expr in enumerate(
            jaff_progress.track(
                radode_symbols, description="Generating radiaton ode code"
            )
        ):
            expr = self.code_gen(expr, strict=False, allow_unknown_functions=True)
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
        """Generate radiation moment ODE assignment code as a multi-line string.

        Wraps :meth:`get_indexed_radodes` and formats the result identically
        to :meth:`get_ode_str`, but for radiation moment equations only.

        Parameters
        ----------
        idx_offset : int, optional
            Base index for the output array subscripts.  Default ``0``.
        use_cse : bool, optional
            Enable CSE.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"rcse"``.
        radode_var : str, optional
            Name of the output radiation ODE array.  Default ``"f"``.
        brac_format : str, optional
            Override 1-D bracket style.  Empty string uses the language default.
        def_prefix : str, optional
            Type declaration prefix for CSE temporaries.  Empty string uses the
            language-default type qualifier and ``double`` type.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.
        order : int, optional
            Radiation moment closure order passed to :meth:`get_indexed_radodes`.
            Default ``0``.

        Returns
        -------
        str
            Multi-line string of radiation ODE assignments including any CSE
            temporaries.
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
        """Return the analytical Jacobian ∂f_i/∂y_j as an :class:`~jaff.types.IndexedReturn`.

        Computes the exact (analytical) Jacobian of the ODE right-hand side
        vector ``f`` with respect to the state vector ``y`` using SymPy's
        symbolic differentiation.  Only non-zero Jacobian elements are
        included in the output, making this suitable for sparse solver formats.

        The computation proceeds in four main stages:

        1. **Symbol mapping** — Each ``nden[i]`` (a SymPy
           :class:`~sympy.MatrixSymbol` entry) is mapped to a scalar symbol
           ``y_i`` to allow :meth:`sympy.Matrix.jacobian` to differentiate
           element-wise.  Radiation density/flux symbols are similarly mapped.
        2. **Rate inlining** — Symbolic rate placeholders ``k[i]`` are
           replaced with the concrete rate expressions after the symbol
           substitution.
        3. **Jacobian computation** — :meth:`sympy.Matrix.jacobian` is called
           on the full ODE vector with respect to ``[y_0, y_1, …]``.
        4. **Back-substitution** — Scalar symbols ``y_i`` in the generated
           code strings are replaced with their original array notation
           ``nden[i]`` (and ``radeden[i]`` / ``rflux[i]`` for radiation) via
           regex.

        When *use_dedt* is ``True``, an extra column ``dẋ_i/dT_gas`` is
        computed using the ideal-gas EOS and inserted after the species
        columns to account for the implicit temperature dependence.

        Parameters
        ----------
        use_dedt : bool, optional
            Include the energy equation in the Jacobian and compute the
            ``dẋ_i/dT_gas`` column via the EOS.  Default ``False``.
        use_cse : bool, optional
            Apply joint CSE across all Jacobian elements.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``.
        specific_eint : bool, optional
            Normalise the energy equation by density (see :meth:`__gen_sdedt`).
            Default ``False``.
        norm : int, optional
            Density normalisation for the energy equation (``0`` or ``1``).
        radiation : bool, optional
            Include radiation moment equations in the Jacobian.
            Default ``False``.
        rad_order : int, optional
            Radiation moment closure order (``0``–``3``).  Used only when
            *radiation* is ``True``.

        Returns
        -------
        IndexedReturn
            Dictionary with:

            * ``"extras"["cse"]`` — CSE temporaries.
            * ``"expressions"`` — non-zero Jacobian elements as
              :class:`~jaff.types.IndexedValue` of ``([row, col], expr_str)``
              pairs.

        Raises
        ------
        ValueError
            If *radiation* is ``True`` and *rad_order* is not in ``{0,1,2,3}``.
        """

        with jaff_progress.indeterminate("Preprocessing jacobian"):
            if radiation and rad_order not in [0, 1, 2, 3]:
                raise ValueError("Invalid order: Supported orders are 0, 1, 2, 3")

            ir: IndexedReturn = {
                "extras": {"cse": IndexedList()},
                "expressions": IndexedList(),
            }
            n_species = self.net.species.count
            n_rad_eqns = (
                2 * self.net.radiation.nbands if radiation and self.net.radiation else 0
            )
            n_ode_eqns = n_species + int(use_dedt) + n_rad_eqns

            # Scalar differentiation symbols for each state variable.
            # SymPy's jacobian() requires ordinary scalar symbols, not
            # MatrixSymbol entries, so we map nden[i] -> y_i temporarily.
            y_syms = [sp.symbols(f"y_{i}") for i in range(n_species)]

            if radiation and self.net.radiation:
                # Pad with placeholder symbols; will be overwritten below
                y_syms.extend([sp.symbols("xx") for _ in range(n_rad_eqns)])

                # Map radiation energy/flux quantities to dedicated scalar symbols
                # ei: energy-density index; fi: flux index (order-dependent)
                for i in range(self.net.radiation.nbands):
                    ei, fi = self.net.radiation.ordered_index(i, rad_order)
                    y_syms[n_species + ei] = sp.symbols(f"ry_{i}")
                    y_syms[n_species + fi] = sp.symbols(f"fy_{i}")

            nden_matrix = sp.MatrixSymbol("nden", n_species, 1)
            # Substitution dicts: MatrixSymbol entries -> scalar y_i symbols
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

            # Substitute nden/radiation symbols inside rate expressions first,
            # then build the subs_k dict that replaces k[i] placeholders in
            # the ODE expressions with those fully-scalar rate expressions.
            k_exprs = [
                rea.rate.xreplace({**nden_to_y, **radden_to_y, **radflux_to_y})
                for rea in self.net.reactions
            ]

            subs_k = {
                sp.symbols(f"k[{i}]"): k_exprs[i] for i in range(len(self.net.reactions))
            }
            ode_symbols = self.net.sodes()

            # Optionally append the energy equation and radiation ODEs
            if use_dedt:
                ode_symbols.append(
                    self.__gen_sdedt(specific_eint=specific_eint, norm=norm)
                )

            if radiation:
                ode_symbols.extend(self.net.sradodes(order=rad_order))

            # Apply all substitutions in a single pass: nden/rad -> y_i, k[i] -> rate
            ode_symbols = [
                sode.xreplace({**nden_to_y, **radden_to_y, **radflux_to_y, **subs_k})
                for sode in ode_symbols
            ]

        with jaff_progress.indeterminate("Generating jacobian"):
            # Compute the full dense Jacobian matrix symbolically
            jacobian_matrix = sp.Matrix(ode_symbols).jacobian(y_syms)

            if use_dedt:
                # Insert the dẋ_i/dT_gas column: convert temperature dependence
                # into the state-vector framework via the ideal-gas EOS relation
                # dẋ_i/dy_e = (dẋ_i/dT_gas) / (de/dT_gas)
                dde = sp.zeros(n_ode_eqns, 1)
                dedot_dtgas = sp.diff(self.__get_sym_eos(), sp.symbols("tgas"))

                for i in range(n_ode_eqns):
                    dxdot_dtgas = sp.diff(ode_symbols[i], sp.symbols("tgas"))
                    dde[i, 0] = dxdot_dtgas / dedot_dtgas
                left = jacobian_matrix[:, :n_species]
                right = jacobian_matrix[:, n_species:]

                # Insert the energy-coupling column between species and radiation cols
                jacobian_matrix = left.row_join(dde).row_join(right)

        # Regex patterns to back-substitute scalar symbols -> array notation in
        # the serialised code strings.
        dpattern = re.compile(r"\by_(\d+)\b")  # y_i -> nden[i]
        if radiation and self.net.radiation is not None:
            rrdpattern = re.compile(r"\bry_(\d+)\b")  # ry_i -> radeden/photden[i]
            rfdpattern = re.compile(r"\bfy_(\d+)\b")  # fy_i -> rflux[i]

        def _replace_y(match: re.Match[str], var) -> str:
            """Regex replacement helper: ``y_N`` → ``var[N]``."""
            idx = int(match.group(1))
            return f"{var}{self.lb}{idx}{self.rb}"

        if use_cse:
            with jaff_progress.indeterminate("Generating cse expressions"):
                cse_var = sp.numbered_symbols(prefix=cse_var)
                replacements, reduced_exprs = sp.cse(
                    list(jacobian_matrix), symbols=cse_var
                )

                replacements = self.__prune_cse(replacements, reduced_exprs)
                # Keep a str-keyed dict so __convert_unknown_derivatives can
                # resolve CSE symbols back to their defining expressions.
                replacements_dict = {str(k): v for k, v in replacements}

                pattern = re.compile(r"(\d+)")
                for var, expr in replacements:
                    # Handle Derivative() nodes arising from user-defined rate
                    # functions before serialisation
                    expr = self.__convert_unknown_derivatives(expr, replacements_dict)
                    match = pattern.search(str(var))
                    idx: int = int(match.group(0)) if match is not None else 0
                    expr_str = self.code_gen(
                        expr, strict=False, allow_unknown_functions=True
                    )
                    # Back-substitute scalar symbols to array notation
                    expr_str = dpattern.sub(lambda m: _replace_y(m, "nden"), expr_str)

                    if radiation and self.net.radiation is not None:
                        rad = self.net.radiation
                        expr_str = rrdpattern.sub(
                            lambda m: _replace_y(
                                m,
                                "radeden" if rad.energy_density else "photden",
                            ),
                            expr_str,
                        )
                        expr_str = rfdpattern.sub(
                            lambda m: _replace_y(m, "rflux"), expr_str
                        )

                    ir["extras"]["cse"].append(IndexedValue([idx], expr_str))

        # Iterate over every (row, col) pair and emit non-zero elements only.
        # Row-major iteration: element [i, j] lives at index i*n + j in the
        # flattened reduced_exprs list produced by sp.cse().
        for i, j in jaff_progress.track(
            product(range(n_ode_eqns), repeat=2), description="Generating jacobian code"
        ):
            expr = reduced_exprs[i * n_ode_eqns + j] if use_cse else jacobian_matrix[i, j]

            # Skip structural zeros to support sparse output formats
            if expr == 0:
                continue

            expr = self.__convert_unknown_derivatives(
                expr, replacements_dict if use_cse else None
            )
            expr_str = self.code_gen(expr, strict=False, allow_unknown_functions=True)
            # Back-substitute scalar y_i -> nden[i] and radiation symbols
            expr_str = dpattern.sub(lambda m: _replace_y(m, "nden"), expr_str)

            if radiation and self.net.radiation is not None:
                rad = self.net.radiation
                expr_str = rrdpattern.sub(
                    lambda m: _replace_y(
                        m,
                        "radeden" if rad.energy_density else "photden",
                    ),
                    expr_str,
                )
                expr_str = rfdpattern.sub(lambda m: _replace_y(m, "rflux"), expr_str)

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
        """Generate Jacobian assignment code as a multi-line string.

        Wraps :meth:`get_indexed_jacobian` and formats the sparse non-zero
        elements as::

            const double cse0 = …;       // CSE temporaries (if any)
            J[0][1] = cse0 * nden[2];    // ∂f_0/∂y_1
            J[2][2] = …;                 // ∂f_2/∂y_2
            …

        Parameters
        ----------
        use_dedt : bool, optional
            Include the energy equation row/column.  Default ``False``.
        idx_offset : int, optional
            Base index for row and column subscripts.  Default ``0``.
        use_cse : bool, optional
            Enable CSE.  Default ``True``.
        cse_var : str, optional
            Prefix for CSE temporary variable names.  Default ``"cse"``.
        jac_var : str, optional
            Name of the Jacobian matrix.  Default ``"J"``.
        matrix_format : str, optional
            Override 2-D bracket/separator format.  Empty string uses the
            language default.
        var_prefix : str, optional
            Type declaration prefix for CSE temporaries.  Empty string uses the
            language-default type qualifier and ``double`` type.
        assignment_op : str, optional
            Assignment operator override.  Empty string uses the language default.
        line_end : str, optional
            Line terminator override.  Empty string uses the language default.

        Returns
        -------
        str
            Multi-line string of Jacobian element assignments including any
            CSE temporaries.

        Raises
        ------
        ValueError
            If *matrix_format* is not a supported format string.
        """
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
    def __convert_unknown_derivatives(
        expr: sp.Expr, cse_defs: dict | None = None
    ) -> sp.Expr:
        """Replace unevaluated SymPy derivatives with named partial-function calls.

        When SymPy differentiates a user-defined function (e.g. a rate that
        calls ``photorates(...)`` or a custom analytic function), it produces
        :class:`~sympy.Derivative` or :class:`~sympy.Subs` nodes that no
        language printer can serialise.  This method replaces each such node
        with a synthetic function whose name encodes the derivative signature::

            Derivative(foo(a, b), a)  →  foo_partial_0(a, b)
            Subs(Derivative(bar(x), x), x, 0)  →  bar_partial_0(a, evaluated_0)

        The suffix ``_N`` indicates that differentiation was performed with
        respect to the argument at position *N*.

        CSE temporaries are resolved (by looking up *cse_defs*) before
        inspecting the inner expression so that derivatives of CSE-reduced
        forms are handled correctly.

        Parameters
        ----------
        expr : sympy.Expr
            Expression potentially containing :class:`~sympy.Derivative` or
            :class:`~sympy.Subs` nodes.
        cse_defs : dict or None, optional
            String-keyed dictionary mapping CSE symbol names to their defining
            expressions (used to resolve CSE references in derivative nodes).
            ``None`` means no CSE context is available.

        Returns
        -------
        sympy.Expr
            Expression with all derivative nodes replaced by named function
            calls that are safe to serialise.
        """
        cse_dict = cse_defs or {}
        replacement_dict = {}

        def _resolve_dexpr(dexpr: sp.Basic) -> sp.Basic:
            """Follow CSE alias chain until a non-alias expression is found."""
            while str(dexpr) in cse_dict:
                dexpr = cse_dict[str(dexpr)]
            return dexpr

        # Handle bare Derivative nodes (not wrapped in Subs)
        for ex in expr.atoms(sp.Derivative):
            dexpr = _resolve_dexpr(ex.expr)

            if (
                not hasattr(dexpr, "func")
                or not hasattr(dexpr.func, "__name__")
                or not hasattr(dexpr, "args")
            ):
                continue

            deriv_name = dexpr.func.__name__
            vars = list(ex.variables)
            args = list(dexpr.args)

            try:
                # Build suffix from argument positions: d/d(arg[k]) -> "_k"
                func_sig_suffix = "_".join([str(args.index(var)) for var in vars])
            except ValueError:
                continue

            new_func_sig = f"{deriv_name}_partial_{func_sig_suffix}"
            new_func = sp.Function(new_func_sig)(*args)  # type: ignore
            replacement_dict[ex] = new_func

        # Handle Subs(Derivative(...), ...) — evaluated derivatives at a point
        for ex in expr.atoms(sp.Subs):
            deriv = ex.args[0]
            if isinstance(deriv, sp.Derivative):
                sub_var = cast(tuple[sp.Basic, ...], ex.args[1])
                sub_val = cast(tuple[sp.Basic, ...], ex.args[2])
                sub_dict = dict(zip(sub_var, sub_val))

                dexpr = _resolve_dexpr(deriv.expr)

                if (
                    not hasattr(dexpr, "func")
                    or not hasattr(dexpr.func, "__name__")
                    or not hasattr(dexpr, "args")
                ):
                    continue

                deriv_name = dexpr.func.__name__
                # Apply the substitution to both the differentiation variables
                # and the function arguments so the new call is fully evaluated
                vars = [var.xreplace(sub_dict) for var in deriv.variables]
                args = [arg.xreplace(sub_dict) for arg in dexpr.args]

                try:
                    func_sig_suffix = "_".join([str(args.index(var)) for var in vars])
                except ValueError:
                    continue

                new_func_sig = f"{deriv_name}_partial_{func_sig_suffix}"

                new_func = sp.Function(new_func_sig)(*args)  # type: ignore
                replacement_dict[ex] = new_func

        expr = expr.xreplace(replacement_dict)

        return expr

    @staticmethod
    def __prune_cse(
        replacements: list[tuple[sp.Symbol, sp.Expr]], expressions: List[sp.Expr]
    ) -> List[Tuple[sp.Symbol, sp.Expr]]:
        """Remove CSE temporaries not transitively used by any reduced expression.

        SymPy's :func:`~sympy.cse` can produce temporaries that are only
        referenced by *other* temporaries that themselves become unreferenced
        after the ``optimizations="basic"`` pass.  This method performs a
        depth-first reachability analysis starting from all free symbols in
        *expressions* and discards every temporary not on a live path.

        Parameters
        ----------
        replacements : list of (sympy.Symbol, sympy.Expr)
            CSE output in order: each tuple ``(tmp_sym, defining_expr)``.
        expressions : list of sympy.Expr
            The CSE-reduced main expressions that reference the temporaries.

        Returns
        -------
        list of (sympy.Symbol, sympy.Expr)
            Subset of *replacements* containing only live temporaries,
            preserving their original order (important for correct emission
            order in the generated code).
        """
        if not replacements:
            return []

        dep_map = dict(replacements)
        cse_syms = set(dep_map.keys())

        used: set = set()

        def _dfs(sym: sp.Symbol) -> None:
            """Recursively mark *sym* and all CSE symbols it depends on as used."""
            if sym in used:
                return
            used.add(sym)

            expr = dep_map.get(sym)
            if expr is None:
                return

            # Recurse into any CSE temporaries appearing inside this definition
            for dep in cast(Set[sp.Symbol], expr.free_symbols & cse_syms):
                _dfs(dep)

        # Seed the reachability search from the main (non-temporary) expressions
        for expr in expressions:
            for sym in cast(Set[sp.Symbol], expr.free_symbols & cse_syms):
                _dfs(sym)

        # Return only live temporaries in their original definition order
        return [(var, dep_map[var]) for var, _ in replacements if var in used]

    @staticmethod
    @cache
    def __get_sym_eos(gamma: float = 1.6666666666667) -> sp.Expr:
        """Return the symbolic ideal-gas specific internal energy.

        Uses the monoatomic-ideal-gas equation of state::

            e = R / (γ − 1) · T_gas   [erg / mol]

        where *R* is the universal gas constant converted to CGS units
        (erg mol⁻¹ K⁻¹) and ``tgas`` is a SymPy symbol for the gas
        temperature in Kelvin.

        This expression is used by :meth:`get_indexed_jacobian` to compute the
        temperature column of the Jacobian via the chain rule:
        ``∂ẋ/∂e = (∂ẋ/∂T) / (∂e/∂T)``.

        The result is cached (via :func:`functools.cache`) because the EOS
        expression is the same for every Jacobian computation.

        Parameters
        ----------
        gamma : float, optional
            Adiabatic index.  Default ``5/3 ≈ 1.6̄`` (monoatomic ideal gas).

        Returns
        -------
        sympy.Expr
            Symbolic expression ``_R / (gamma - 1) * tgas``.
        """
        from scipy.constants import R

        _R = R * 1e7  # Convert J/(mol·K) -> erg/(mol·K)
        tgas = sp.symbols("tgas")

        return _R / (gamma - 1) * tgas

    @staticmethod
    @cache
    def __get_language_aliases() -> dict[str, str]:
        """Return the mapping from user-facing language aliases to canonical names.

        Allows callers to use common shorthand spellings (``"c++"``, ``"py"``,
        ``"rs"``, ``"f90"``, …) and normalise them to the internal canonical
        name used as a key in :meth:`get_language_tokens`.

        Returns
        -------
        dict[str, str]
            Mapping of alias -> canonical language name.
        """
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
        """Return the :class:`LangModifier` configuration for every supported language.

        Each entry in the returned dict captures the syntax conventions needed
        to emit valid code for that language: brackets, assignment operator,
        line terminator, 2-D matrix separator, SymPy code-gen function, index
        base offset, comment character, type keywords, and miscellaneous extras.

        The result is cached (via :func:`functools.cache`) because it is a
        pure constant table.  Callers should use canonical language names
        (``"cxx"``, ``"c"``, ``"fortran"``, ``"python"``, ``"rust"``,
        ``"julia"``, ``"r"``) as keys; use :meth:`__get_language_aliases` to
        map user-facing aliases first.

        Returns
        -------
        dict[str, LangModifier]
            Mapping of canonical language name -> :class:`LangModifier`.

        Notes
        -----
        Index offsets:
            * ``0`` for 0-based languages: C, C++, Python, Rust.
            * ``1`` for 1-based languages: Fortran, Julia, R.
        """
        tokens: dict[str, LangModifier] = {
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
        """Return supported 2-D array bracket/separator format strings.

        Each entry maps a format key (as accepted by the *matrix_format*
        constructor argument) to a ``{"brac": "…", "sep": "…"}`` dict where
        ``brac`` is the two-character bracket pair and ``sep`` is the string
        inserted between the row and column indices.

        For example, ``"(,)"`` yields ``J(i, j)`` while ``"[]"`` yields
        ``J[i][j]``.

        Returns
        -------
        dict[str, dict[str, str]]
            Mapping of format key -> ``{"brac": str, "sep": str}``.
        """
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
        """Return the list of supported 1-D array bracket styles.

        Returns
        -------
        list[str]
            Each string is a two-character bracket pair accepted by the
            *brac_format* constructor argument.
        """
        formats: list[str] = ["()", "{}", "[]", "<>"]

        return formats
