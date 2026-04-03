#ifndef actual_rhs_H
#define actual_rhs_H

#include <AMReX_Array.H>
#include <AMReX_REAL.H>
#include <cmath>

#include <actual_network.H>
#include <burn_type.H>
#include <extern_parameters.H>
#include <jacobian_utilities.H>

using namespace ArrayUtil;
using namespace network_rp;

AMREX_GPU_HOST_DEVICE AMREX_INLINE amrex::Real photorates() { return 0.0; }

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
rhs_specie(const burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot,
           const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden) {

  using namespace Rates;

  amrex::Real tgas = state.T;
  amrex::Real crate = 0.0; // placeholder
  amrex::Real av = 0.0;    // placeholder

  // $JAFF REPEAT idx, rhs, cse IN rhses $[REPLACE radeden\[\s*(\d+)\s*\] radeden(\1) REPLACE rflux\[\s*(\d+)\s*\] rflux(\1) REPLACE nden\[\s*(\d+)\s*\] nden(\1) RADIATION True]$
  const amrex::Real cse$idx$ = $cse$;
  ydot($idx+1$) = $rhs$;
  // $JAFF END
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
actual_rhs(burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot) {

  amrex::Array1D<amrex::Real, 0, NumSpec - 1> nden;
  for (int i = 0; i < NumSpec; ++i) {
    nden(i) = state.xn[i];
  }

  // YDOTS
  rhs_specie(state, ydot, nden);
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void
jac_chem(const burn_t &state, MatrixType &jac,
         const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden) {

  amrex::Real tgas = state.T;
  amrex::Real crate = 0.0; // placeholder
  amrex::Real av = 0.0;    // placeholder

  // $JAFF REPEAT idx, expr, cse IN jacobian $[REPLACE nden\[\s*(\d+)\s*\] nden(\1) USE_DEDT True]$
  const amrex::Real cse$idx$ = $cse$;
  jac($idx+1$, $idx+1$) = $expr$;
  // $JAFF END
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void actual_jac(const burn_t &state,
                                                   MatrixType &jac) {

  amrex::Array1D<amrex::Real, 0, NumSpec - 1> nden;
  for (int i = 0; i < NumSpec; ++i) {
    nden(i) = state.xn[i];
  }

  jac.zero();
  // Species Jacobian elements with respect to other species

  jac_chem(state, jac, nden);
}

AMREX_INLINE
void actual_rhs_init() {}

#endif
