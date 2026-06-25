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

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
actual_rhs(const burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot) {

  using namespace Rates;

  // $JAFF REPEAT idx, rhs, cse IN rhses $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1] REPLACE tgas state.T RADIATION True]$
  const amrex::Real cse$idx$ = $cse$;
  ydot($idx+1$) = $rhs$;
  // $JAFF END
  // $JAFF SUB nspec
  ydot($nspec+1$) /= state.rho;
  // $JAFF END
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
actual_rhs_qss(const burn_t &state, amrex::Array1D<amrex::Real, 1, 2 * neqs> &ydot) {

  using namespace Rates;

  amrex::Real tgas = state.T;

  amrex::Array1D<amrex::Real, 0, NumSpec - 1> nden;
      for (int i = 0; i < NumSpec; ++i) {
      nden(i) = state.xn[i];
      }
  amrex::Real l0_co_interp1d = l0_co_interp1d_func(state);
  amrex::Real llte_co_interp2d = llte_co_interp2d_func(state, nden);
  amrex::Real psigd_coll_interp2d = psigd_coll_interp2d_func(state, nden);
  amrex::Real alpha_co_interp2d = alpha_co_interp2d_func(state, nden);
  amrex::Real nhalf_co_interp2d = nhalf_co_interp2d_func(state, nden);


  amrex::Real crate = network_rp::crate;
  amrex::Real av = network_rp::Av;
  amrex::Real d2g = network_rp::dust2gas_ratio;
  amrex::Real chi = network_rp::chi;

  const double Leff_CO_max_ = 3.0e20; //Maximum CO cooling length. default 100pc.
  const double gradv_ =  3 * 3e-14; //1.0e-14 = 0.3km/s /pc*/
  const double kb_ = 1.380649e-16; // Boltzmann constant in erg/K
  const double mCO_ = 4.68e-23; // mass of CO molecule
  const double vth = sqrt(2. * kb_ * tgas / mCO_);

  const double grad_small = vth / Leff_CO_max_;
  const double gradeff = std::max(gradv_, grad_small);
  const double gradv = gradeff;

  // $JAFF REPEAT idx, rhs, cse IN qss_rhses $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1]]$
  const amrex::Real qss_cse$idx$ = $cse$;
  ydot($idx+1$) = $rhs$;
  // $JAFF END
  // $JAFF SUB nspec, dedt $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1]]$
  const amrex::Real qss_dedt = $dedt$ / state.rho;
  ydot(2 * ($nspec$ + 1) - 1) = amrex::max(qss_dedt, amrex::Real(0.0));
  ydot(2 * ($nspec$ + 1)) = amrex::max(-qss_dedt, amrex::Real(0.0));
  // $JAFF END
  // $JAFF REPEAT idx, rhs, cse IN qss_rad_rhses $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1]]$
  const amrex::Real qss_rad_cse$idx$ = $cse$;
  ydot($idx+1$) = $rhs$;
  // $JAFF END
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void actual_jac(const burn_t &state,
                                                   MatrixType &jac) {

  // $JAFF REPEAT idx, expr, cse IN jacobian $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1] REPLACE tgas state.T RADIATION True USE_DEDT True]$
  const amrex::Real cse$idx$ = $cse$;
  jac($idx+1$, $idx+1$) = $expr$;
  // $JAFF END
  // $JAFF SUB nspec, nbands
  int total_eqns = $nspec$ + $nbands*2$ + 1;
  for (int i = 1; i <= total_eqns; i++) {
    jac(i, $nspec+1$) /= state.rho;
  }

  for (int i = 1; i <= total_eqns; i++) {
    if (i == $nspec+1$) { continue; }
    jac($nspec+1$, i) /= state.rho;
  }
  // $JAFF END

}

AMREX_INLINE
void actual_rhs_init() {}

#endif
