---
tags:
    - User-guide
    - Code-generation
---

# Worked Example

This page walks one toy example: a tiny network, a C++ template, the
[`jaffgen`](jaffgen.md) command that expands it,
and the compiled program that integrates the chemistry.

The mental model is the only thing to hold onto: **a template is ordinary source
code; every line is copied to the output verbatim except the `$JAFF` blocks,
which are expanded against the network.** The
[Template Syntax](template-syntax.md) page is the
full directive reference; this page just puts the pieces together.

---

## 1. The network

A two-species, two-reaction network: hydrogen atoms forming H₂ and H₂ breaking
back apart. Save it as `toy.jet`:

```text
# Toy H2 formation/dissociation network (PRIZMO format)
# columns:  reaction  [tmin,tmax]  rate-coefficient(tgas)
H + H -> H2     []   1.00e-10*(tgas/3e2)**(-0.5)
H2 -> H + H     []   2.00e-9*exp(-1.0e2/tgas)
```

Both rates are plain functions of the gas temperature `tgas`, so the generated
code is self-contained — no photochemistry, cosmic-ray, or extinction symbols to
supply at runtime. Species are indexed in load order: `H` is `0`, `H2` is `1`.

---

## 2. The template

One file does everything: the species/reaction counts, the ODE right-hand side,
the analytic Jacobian, and an implicit backward-Euler driver. Save it as
`solver.cpp`. The `$JAFF` blocks are the only generated regions — everything
else is C++ copied through untouched.

```cpp
// solver.cpp — a JAFF template.
// Every line is plain C++ and copied verbatim, except the $JAFF blocks,
// which JAFF fills in from the network.
#include <cstdio>
#include <cmath>

// $JAFF SUB nspec, nreact
#define NSPEC  $nspec$
#define NREACT $nreact$
// $JAFF END

// dn/dt for every species. nden[] = number densities (cm^-3), tgas = K.
void derivatives(const double nden[NSPEC], double tgas, double f[NSPEC]) {
    // $JAFF REPEAT idx, ode IN odes
    f[$idx$] = $ode$;
    // $JAFF END
}

// Analytic Jacobian J[i][j] = d f[i] / d nden[j]. Only non-zero entries are
// generated; the rest stay zero from the clear loop.
void jacobian(const double nden[NSPEC], double tgas, double J[NSPEC][NSPEC]) {
    for (int i = 0; i < NSPEC; ++i)
        for (int j = 0; j < NSPEC; ++j) J[i][j] = 0.0;
    // $JAFF REPEAT idx, expr IN jacobian
    J[$idx$][$idx$] = $expr$;
    // $JAFF END
}

// --- plain C++ below: a backward-Euler driver, copied through untouched ---

// Solve A x = b in place for an NSPEC-square system (Gaussian elimination
// with partial pivoting). b holds the solution on return.
static void solve(double A[NSPEC][NSPEC], double b[NSPEC]) {
    for (int col = 0; col < NSPEC; ++col) {
        int piv = col;
        for (int r = col + 1; r < NSPEC; ++r)
            if (std::fabs(A[r][col]) > std::fabs(A[piv][col])) piv = r;
        for (int c = 0; c < NSPEC; ++c) { double t = A[col][c]; A[col][c] = A[piv][c]; A[piv][c] = t; }
        double t = b[col]; b[col] = b[piv]; b[piv] = t;
        for (int r = col + 1; r < NSPEC; ++r) {
            double m = A[r][col] / A[col][col];
            for (int c = col; c < NSPEC; ++c) A[r][c] -= m * A[col][c];
            b[r] -= m * b[col];
        }
    }
    for (int r = NSPEC - 1; r >= 0; --r) {
        double s = b[r];
        for (int c = r + 1; c < NSPEC; ++c) s -= A[r][c] * b[c];
        b[r] = s / A[r][r];
    }
}

int main() {
    double nden[NSPEC] = {1.0e6, 0.0};   // start fully atomic: H, H2
    const double tgas = 3.0e2;           // 300 K
    const double dt   = 1.0e3;           // s
    const int    nsteps = 200;

    // One backward-Euler step: solve nden_new - nden - dt*f(nden_new) = 0 for
    // nden_new by Newton iteration. The Newton matrix is I - dt*J.
    auto step = [&](double y[NSPEC]) {
        double yn[NSPEC];
        for (int i = 0; i < NSPEC; ++i) yn[i] = y[i];   // initial guess
        for (int it = 0; it < 8; ++it) {
            double f[NSPEC], J[NSPEC][NSPEC], G[NSPEC][NSPEC], res[NSPEC];
            derivatives(yn, tgas, f);
            jacobian(yn, tgas, J);
            for (int i = 0; i < NSPEC; ++i) {
                res[i] = -(yn[i] - y[i] - dt * f[i]);
                for (int j = 0; j < NSPEC; ++j)
                    G[i][j] = (i == j ? 1.0 : 0.0) - dt * J[i][j];
            }
            solve(G, res);                  // res <- Newton update
            double norm = 0.0;
            for (int i = 0; i < NSPEC; ++i) { yn[i] += res[i]; norm += std::fabs(res[i]); }
            if (norm < 1.0e-6) break;
        }
        for (int i = 0; i < NSPEC; ++i) y[i] = yn[i];
    };

    printf("%10s %12s %12s %14s\n", "t[s]", "n(H)", "n(H2)", "H_nuclei");
    for (int s = 0; s <= nsteps; ++s) {
        if (s % 40 == 0)
            printf("%10.0f %12.4e %12.4e %14.6e\n",
                   s*dt, nden[0], nden[1], nden[0] + 2*nden[1]);
        step(nden);
    }
    return 0;
}
```

Three directives carry the whole example:

- **`SUB nspec, nreact`** swaps the `$nspec$` / `$nreact$` tokens for the counts.
- **`REPEAT idx, ode IN odes`** emits one `f[$idx$] = $ode$;` line per species,
  filling `$idx$` with the species index and `$ode$` with the full
  dn/dt expression. The
  [`odes`](template-syntax.md#expression-generating-collections)
  collection inlines the rate coefficients, so the rates never need a separate
  array here.
- **`REPEAT idx, expr IN jacobian`** emits the analytic Jacobian. It is a 2D
  collection, so the body carries two `$idx$` tokens (row, column) and one
  `$expr$`. JAFF differentiates the ODEs symbolically and writes only the
  **non-zero** `J[i][j]` entries — which is why the function clears `J` to zero
  first. The implicit driver needs this matrix; an explicit method would not.

The comment token (`//`) is read from the `.cpp` extension; JAFF recognises a
directive only when a line begins with it immediately followed by `$JAFF`. The
generated code uses the names `nden` and `tgas`, so the driver below speaks the
same names — no remapping needed.

<!-- prettier-ignore -->
!!! tip "Renaming JAFF's symbols"
    To target a codebase that calls the density array `y` and the temperature
    `T`, add a `REPLACE` modifier instead of renaming by hand:
    `#!text // $JAFF REPEAT idx, ode IN odes $[REPLACE nden y REPLACE tgas T]$`.
    See [REPLACE](template-syntax.md#replace-directive).

---

## 3. Generate

Run `jaffgen` over the template, pointing it at the network:

```bash
jaffgen --network toy.jet --files solver.cpp --outdir generated/
```

```text
INFO     Network loaded successfully!
INFO     solver.cpp created at .../generated
INFO     Successfully generated files
```

The expanded file keeps its name and lands in `generated/solver.cpp`. The
directive lines survive in the output (as comments), with the generated content
spliced in beneath them:

```cpp
// $JAFF SUB nspec, nreact
#define NSPEC  2
#define NREACT 2
// $JAFF END

// dn/dt for every species. nden[] = number densities (cm^-3), tgas = K.
void derivatives(const double nden[NSPEC], double tgas, double f[NSPEC]) {
    // $JAFF REPEAT idx, ode IN odes
    f[0] = -3.4641016151377544e-9*std::pow(tgas, -0.5)*std::pow(nden[0], 2) + 4.0000000000000002e-9*std::exp(-100.0/tgas)*nden[1];
    f[1] = 1.7320508075688772e-9*std::pow(tgas, -0.5)*std::pow(nden[0], 2) - 2.0000000000000001e-9*std::exp(-100.0/tgas)*nden[1];
    // $JAFF END
}

// Analytic Jacobian J[i][j] = d f[i] / d nden[j]. Only non-zero entries are
// generated; the rest stay zero from the clear loop.
void jacobian(const double nden[NSPEC], double tgas, double J[NSPEC][NSPEC]) {
    for (int i = 0; i < NSPEC; ++i)
        for (int j = 0; j < NSPEC; ++j) J[i][j] = 0.0;
    // $JAFF REPEAT idx, expr IN jacobian
    J[0][0] = -6.9282032302755089e-9*std::pow(tgas, -0.5)*nden[0];
    J[0][1] = 4.0000000000000002e-9*std::exp(-100.0/tgas);
    J[1][0] = 3.4641016151377544e-9*std::pow(tgas, -0.5)*nden[0];
    J[1][1] = -2.0000000000000001e-9*std::exp(-100.0/tgas);
    // $JAFF END
}
```

Each `J[i][j]` is the partial derivative of `f[i]` with respect to `nden[j]` —
here all four entries are non-zero, but on a real network the Jacobian is sparse
and JAFF emits only the entries that survive differentiation.

Everything outside the three blocks — the includes, the `derivatives` /
`jacobian` signatures, the whole backward-Euler `main` — is byte-for-byte the
template.

---

## 4. Plug it into a codebase

Because the template already bundles a `main`, the generated file is a complete
program: compile and run it with nothing else.

```bash
g++ -O2 -std=c++17 generated/solver.cpp -o toy_solver
./toy_solver
```

```text
      t[s]         n(H)        n(H2)       H_nuclei
         0   1.0000e+06   0.0000e+00   1.000000e+06
     40000   1.1649e+05   4.4175e+05   1.000000e+06
     80000   6.0802e+04   4.6960e+05   1.000000e+06
    120000   4.1075e+04   4.7946e+05   1.000000e+06
    160000   3.1012e+04   4.8449e+05   1.000000e+06
    200000   2.4920e+04   4.8754e+05   1.000000e+06
```

The atomic hydrogen converts to H₂ and settles toward chemical equilibrium, and
the last column — total H nuclei, `n(H) + 2·n(H2)` — stays pinned at `1.0e6`,
the conservation check that says the integrator and the generated right-hand
side agree. Plotting every step makes the approach to equilibrium plain:

![Abundances of H and H₂ versus time, relaxing to chemical equilibrium](../../assets/toy_abundances_light.png#only-light){ width="640" }
![Abundances of H and H₂ versus time, relaxing to chemical equilibrium](../../assets/toy_abundances_dark.png#only-dark){ width="640" }

In a real project you would not generate `main`. Drop the directive blocks into
a header your code already owns:

```cpp
// chem_rhs.hpp — generated by JAFF; do not edit by hand.
#pragma once
#include <cmath>

// $JAFF SUB nspec
#define NSPEC $nspec$
// $JAFF END

inline void derivatives(const double nden[NSPEC], double tgas, double f[NSPEC]) {
    // $JAFF REPEAT idx, ode IN odes
    f[$idx$] = $ode$;
    // $JAFF END
}

inline void jacobian(const double nden[NSPEC], double tgas, double J[NSPEC][NSPEC]) {
    for (int i = 0; i < NSPEC; ++i)
        for (int j = 0; j < NSPEC; ++j) J[i][j] = 0.0;
    // $JAFF REPEAT idx, expr IN jacobian
    J[$idx$][$idx$] = $expr$;
    // $JAFF END
}
```

Now your own integrator, time-stepping loop, or hydro code includes
`chem_rhs.hpp` and calls `derivatives(...)` / `jacobian(...)` — and re-running
`jaffgen` after a network change regenerates the header in place, leaving the
surrounding code untouched. Regenerating is the point: the chemistry stays in
the network file, the C++ stays in your repo, and the two are kept in sync by a
single command.

<!-- prettier-ignore -->
!!! warning "This is just a toy network"
    The backward-Euler step above is deliberately minimal — a fixed step size
    and a dense linear solve. Real astrochemical networks are stiff and want a
    production integrator with adaptive stepping and sparse linear algebra.

---

## See also

- [Template Syntax](template-syntax.md) — every directive, collection, and modifier.
- [jaffgen CLI](jaffgen.md) — inputs, built-in templates, and options.
- [`Codegen`](../../api/codegen/codegen/index.md) — the low-level generator behind the `odes`/`rates`/`jacobian` collections.
- [`Builder`](../../api/codegen/builder/index.md) — ready-made solver templates when you don't want to write your own.
