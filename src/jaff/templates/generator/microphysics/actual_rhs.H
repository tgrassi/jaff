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

AMREX_GPU_HOST_DEVICE AMREX_INLINE static int
LinearInterpIndex_(const int len, const double xarr[],
                                 const double x){
      int i = 0;
      if ( x < xarr[0]) {
        return 0;
      } else if ( x > xarr[len-1]) {
        return len-2;
      } else {
        for (i=0; x>xarr[i]; i++) {}
        return i-1;
      }
    }

AMREX_GPU_HOST_DEVICE AMREX_INLINE static amrex::Real
LinearInterp_(const double x0, const double x1,
                               const double y0, const double y1,
                               const double x){
      return y0 + ( (y1-y0)/(x1-x0) ) * (x-x0);
    }

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
LP1Di_(const double *xarr, const double *data, const int ix,
                     const double x) {
  return LinearInterp_(xarr[ix], xarr[ix+1], data[ix], data[ix+1], x);
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
LP2Di_(const double *xarr, const double *yarr,
                      const int lenx, const int ix, const int iy,
                      const double *data, const double x, const double y) {
  double fl1, fl2;
  const double x0 = xarr[ix];
  const double x1 = xarr[ix+1];
  fl1 = LinearInterp_(x0, x1, data[iy*lenx + ix], data[iy*lenx + ix+1], x);
  fl2 = LinearInterp_(x0, x1, data[(iy+1)*lenx + ix], data[(iy+1)*lenx + ix+1], x);
  return LinearInterp_(yarr[iy], yarr[iy+1], fl1, fl2, y);
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
LP2D(const int lenx, const double *xarr,
                    const int leny, const double *yarr,
                    const double *data, const double x, const double y) {
  const int ix = LinearInterpIndex_(lenx, xarr, x);
  const int iy = LinearInterpIndex_(leny, yarr, y);
  return LP2Di_(xarr, yarr, lenx, ix, iy, data, x, y);
}

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
psigd_coll_interp2d_func(const burn_t &state, const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden){
  const amrex::Real lognHi = log10(nden(0));
  const amrex::Real logTgi = log10(state.T);

  const int lenTg_ = 10;
  const int lennH_ = 15;

  const double logTg_[lenTg_] = {
    0.5       , 0.88888889, 1.27777778, 1.66666667, 2.05555556,  2.44444444,
    2.83333333, 3.22222222, 3.61111111, 4.
  };
  const double lognH_[lennH_] = {
    0.        , 0.42857143, 0.85714286, 1.28571429, 1.71428571, 2.14285714,
    2.57142857, 3.        , 3.42857143, 3.85714286, 4.28571429, 4.71428571,
    5.14285714, 5.57142857, 6.
  };
  const double logps_[lennH_ * lenTg_] = {
   33.60923439, 32.35048647, 31.6458604 , 31.02132235, 30.42222289 ,
   29.83261   , 29.24673384, 28.66235604, 28.0785789 , 27.49504472 ,
   33.18091039, 31.92216147, 31.21753302, 30.59298934, 29.99387726 ,
   29.40423904, 28.8183211 , 28.23389204, 27.65007024, 27.06650687 ,
   32.75300149, 31.49424423, 30.78959638, 30.16501048, 29.5658181  ,
   28.97605855, 28.39000596, 27.80546791, 27.22157705, 26.6379757  ,
   32.32619855, 31.06738031, 30.36260198, 29.73777592, 29.13823862 ,
   28.54811853, 27.96178914, 27.37708183, 26.79309991, 26.20945204 ,
   31.90230918, 30.64308622, 29.93758718, 29.3117745 , 28.71125923 ,
   28.12042115, 27.53366605, 26.94873467, 26.36464058, 25.78093706 ,
   31.48587783, 30.22433325, 29.51586354, 28.88730605, 28.28488476 ,
   27.69295575, 27.10563836, 26.52043033, 25.93620173, 25.35243225 ,
   31.0872853 , 29.81525158, 29.09829079, 28.46439304, 27.85909326 ,
   27.26572717, 26.67771529, 26.09217504, 25.50778679, 24.92393938 ,
   30.72591396, 29.41932635, 28.68506438, 28.0430074 , 27.4339034  ,
   26.83875916, 26.24991203, 25.66397699, 25.07939997, 24.49546057 ,
   30.42733764, 29.03861249, 28.27630163, 27.62323376, 27.00938204 ,
   26.41209045, 25.82224861, 25.23584618, 24.65104624, 24.06699834 ,
   30.21146872, 28.67535786, 27.87248634, 27.20529029, 26.58563564 ,
   25.9857724 , 25.39474974, 24.80779463, 24.22273154, 23.63855567 ,
   30.08004755, 28.33375429, 27.47457781, 26.78951505, 26.16280582 ,
   25.55986866, 24.96744513, 24.37983659, 23.79446288, 23.21013604 ,
   30.0136033 , 28.02095875, 27.08405993, 26.37636621, 25.74107062 ,
   25.13445646, 24.54037027, 23.95198897, 23.36624852, 22.7817436  ,
   29.98466705, 27.74775444, 26.70307122, 25.96644194, 25.32065037 ,
   24.70962891, 24.1135674 , 23.52427179, 22.93809825, 22.35338321 ,
   29.97312226, 27.52792637, 26.3346648 , 25.56052005, 24.90181737 ,
   24.28549826, 23.68708687, 23.09670875, 22.51002362, 21.92506064 ,
   29.96870043, 27.37312455, 25.98324711, 25.15962125, 24.48490972 ,
   23.86220014, 23.26098873, 22.66932799, 22.08203828, 21.49678269 ,
  };

  const amrex::Real logpsi = LP2D(lenTg_, logTg_, lennH_, lognH_, logps_,
                                     logTgi, lognHi);
  return pow(10.0, - logpsi);

}

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
l0_co_interp1d_func(const burn_t &state){

   const double Tmax_CO = 2000.; //maximum temperature above which use Tmax
   double T = 0;;
   if (state.T < Tmax_CO) {
     T = state.T;
   } else {
     T = Tmax_CO;
   }

   const int lenTCO_ = 11;

   const double TCO_[lenTCO_] = {10,	20,	30,	50,	80,	100,
                                      300,	600,	1000,	1500,	2000};

   const int iT0 =  LinearInterpIndex_(lenTCO_, TCO_, T);

   const double L0CO_[lenTCO_] = {24.77,	24.38, 24.21,	24.03, 23.89, 23.82,
    /* values from despotic, behaves better at high temperature*/
    23.34238089,  22.99832519,  22.75384686,  22.56640625, 22.43740866};

   const amrex::Real log_L0 = - LP1Di_(TCO_, L0CO_, iT0, T);
   const amrex::Real L0 = pow(10, log_L0);

   return L0;
}


AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
llte_co_interp2d_func(const burn_t &state, const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden){

   const double Tmax_CO = 2000.; //maximum temperature above which use Tmax
   double T = 0;;
   if (state.T < Tmax_CO) {
     T = state.T;
   } else {
     T = Tmax_CO;
   }


   const double Leff_CO_max_ = 3.0e20; //Maximum CO cooling length. default 100pc.
   const double gradv_ =  3 * 3e-14; //1.0e-14 = 0.3km/s /pc*/
   const double amu = 1.66053906660e-24; // atomic mass unit in g
   const double kb_ = 1.380649e-16; // Boltzmann constant in erg/K
   const double mCO_ = 4.68e-23; // mass of CO molecule in amu
   const double vth = sqrt(2. * kb_ * T / mCO_);

   const double grad_small = vth / Leff_CO_max_;
   const double gradeff = std::max(gradv_, grad_small);

   const amrex::Real n_CO = nden(9); // CO number density
   const amrex::Real NCOeff = n_CO / gradeff;


   const int lenTCO_ = 11;

   const double TCO_[lenTCO_] = {10,	20,	30,	50,	80,	100,
                                      300,	600,	1000,	1500,	2000};

   const int iT0 =  LinearInterpIndex_(lenTCO_, TCO_, T);

   const int lenNeffCO_ = 11;

   const double NeffCO_[lenNeffCO_] = {14.0, 14.5, 15.0, 15.5, 16.0, 16.5,
                                            17.0, 17.5, 18.0, 18.5, 19.0};

   const double eps = 1.0e13;
   const double log_NCOeff = log10(NCOeff*1.0e5 + eps); /*unit: cm^-2 / (km/s) */

   const int iNeff0 = LinearInterpIndex_(lenNeffCO_, NeffCO_, log_NCOeff);


   const double LLTECO_[lenNeffCO_*lenTCO_] = {
   21.08, 20.35, 19.94, 19.45, 19.01, 18.80, 17.81, 17.23, 16.86, 16.66, 16.55,
   21.09, 20.35, 19.95, 19.45, 19.01, 18.80, 17.81, 17.23, 16.86, 16.66, 16.55,
   21.11, 20.37, 19.96, 19.46, 19.01, 18.80, 17.81, 17.23, 16.86, 16.66, 16.55,
   21.18, 20.40, 19.98, 19.47, 19.02, 18.81, 17.82, 17.23, 16.87, 16.66, 16.55,
   21.37, 20.51, 20.05, 19.52, 19.05, 18.83, 17.82, 17.23, 16.87, 16.66, 16.55,
   21.67, 20.73, 20.23, 19.64, 19.13, 18.90, 17.85, 17.25, 16.88, 16.67, 16.56,
   22.04, 21.05, 20.52, 19.87, 19.32, 19.06, 17.92, 17.28, 16.90, 16.69, 16.58,
   22.44, 21.42, 20.86, 20.19, 19.60, 19.33, 18.08, 17.38, 16.97, 16.75, 16.63,
   22.87, 21.82, 21.24, 20.55, 19.95, 19.66, 18.34, 17.59, 17.15, 16.91, 16.78,
   23.30, 22.23, 21.65, 20.94, 20.32, 20.03, 18.67, 17.89, 17.48, 17.26, 17.12,
   23.76, 22.66, 22.06, 21.35, 20.71, 20.42, 19.03, 18.26, 17.93, 17.74, 17.61
   };

   const amrex::Real log_LLTE = - LP2Di_(TCO_, NeffCO_, lenTCO_, iT0, iNeff0,
                                           LLTECO_, T, log_NCOeff);
   const amrex::Real LLTE = pow(10, log_LLTE);

   return LLTE;

}


AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
alpha_co_interp2d_func(const burn_t &state, const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden){

   const double Tmax_CO = 2000.; //maximum temperature above which use Tmax
   double T = 0;;
   if (state.T < Tmax_CO) {
     T = state.T;
   } else {
     T = Tmax_CO;
   }

   const double Leff_CO_max_ = 3.0e20; //Maximum CO cooling length. default 100pc.
   const double gradv_ =  3 * 3e-14; //1.0e-14 = 0.3km/s /pc*/
   const double amu = 1.66053906660e-24; // atomic mass unit in g
   const double kb_ = 1.380649e-16; // Boltzmann constant in erg/K
   const double mCO_ = 4.68e-23; // mass of CO molecule in amu
   const double vth = sqrt(2. * kb_ * T / mCO_);

   const double grad_small = vth / Leff_CO_max_;
   const double gradeff = std::max(gradv_, grad_small);

   const amrex::Real n_CO = nden(9); // CO number density
   const amrex::Real NCOeff = n_CO / gradeff;


   const int lenTCO_ = 11;

   const double TCO_[lenTCO_] = {10,	20,	30,	50,	80,	100,
                                      300,	600,	1000,	1500,	2000};

   const int iT0 =  LinearInterpIndex_(lenTCO_, TCO_, T);

   const int lenNeffCO_ = 11;

   const double NeffCO_[lenNeffCO_] = {14.0, 14.5, 15.0, 15.5, 16.0, 16.5,
                                            17.0, 17.5, 18.0, 18.5, 19.0};

   const double eps = 1.0e13;
   const double log_NCOeff = log10(NCOeff*1.0e5 + eps); /*unit: cm^-2 / (km/s) */

   const int iNeff0 = LinearInterpIndex_(lenNeffCO_, NeffCO_, log_NCOeff);


   const double alphaCO_[lenNeffCO_*lenTCO_] = {
   0.439, 0.409, 0.392, 0.370, 0.361, 0.357, 0.385, 0.437, 0.428, 0.354, 0.322,
   0.436, 0.407, 0.391, 0.368, 0.359, 0.356, 0.385, 0.437, 0.427, 0.354, 0.322,
   0.428, 0.401, 0.385, 0.364, 0.356, 0.352, 0.383, 0.436, 0.427, 0.352, 0.320,
   0.416, 0.388, 0.373, 0.353, 0.347, 0.345, 0.380, 0.434, 0.425, 0.349, 0.316,
   0.416, 0.378, 0.360, 0.338, 0.332, 0.330, 0.371, 0.429, 0.421, 0.341, 0.307,
   0.450, 0.396, 0.367, 0.334, 0.322, 0.317, 0.355, 0.419, 0.414, 0.329, 0.292,
   0.492, 0.435, 0.403, 0.362, 0.339, 0.329, 0.343, 0.406, 0.401, 0.317, 0.276,
   0.529, 0.473, 0.441, 0.404, 0.381, 0.370, 0.362, 0.410, 0.392, 0.316, 0.272,
   0.555, 0.503, 0.473, 0.440, 0.423, 0.414, 0.418, 0.446, 0.404, 0.335, 0.289,
   0.582, 0.528, 0.499, 0.469, 0.457, 0.451, 0.470, 0.487, 0.432, 0.364, 0.310,
   0.596, 0.546, 0.519, 0.492, 0.483, 0.479, 0.510, 0.516, 0.448, 0.372, 0.313
   };

   const amrex::Real alpha = LP2Di_(TCO_, NeffCO_, lenTCO_, iT0, iNeff0,
                                      alphaCO_, T, log_NCOeff);

   return alpha;

}

AMREX_GPU_HOST_DEVICE AMREX_INLINE  amrex::Real
nhalf_co_interp2d_func(const burn_t &state, const amrex::Array1D<amrex::Real, 0, NumSpec - 1> &nden){

   const double Tmax_CO = 2000.; //maximum temperature above which use Tmax
   double T = 0;;
   if (state.T < Tmax_CO) {
     T = state.T;
   } else {
     T = Tmax_CO;
   }

   const double Leff_CO_max_ = 3.0e20; //Maximum CO cooling length. default 100pc.
   const double gradv_ =  3 * 3e-14; //1.0e-14 = 0.3km/s /pc*/
   const double kb_ = 1.380649e-16; // Boltzmann constant in erg/K
   const double mCO_ = 4.68e-23; // mass of CO molecule
   const double vth = sqrt(2. * kb_ * T / mCO_);

   const double grad_small = vth / Leff_CO_max_;
   const double gradeff = std::max(gradv_, grad_small);

   const amrex::Real n_CO = nden(9); // CO number density
   const amrex::Real NCOeff = n_CO / gradeff;

   const int lenTCO_ = 11;

   const double TCO_[lenTCO_] = {10,	20,	30,	50,	80,	100,
                                      300,	600,	1000,	1500,	2000};

   const int iT0 =  LinearInterpIndex_(lenTCO_, TCO_, T);

   const int lenNeffCO_ = 11;

   const double NeffCO_[lenNeffCO_] = {14.0, 14.5, 15.0, 15.5, 16.0, 16.5,
                                            17.0, 17.5, 18.0, 18.5, 19.0};

   const double eps = 1.0e13;
   const double log_NCOeff = log10(NCOeff*1.0e5 + eps); /*unit: cm^-2 / (km/s) */

   const int iNeff0 = LinearInterpIndex_(lenNeffCO_, NeffCO_, log_NCOeff);


   const double nhalfCO_[lenNeffCO_*lenTCO_] = {
   3.29, 3.49 ,3.67  ,3.97,  4.30, 4.46, 5.17, 5.47, 5.53, 5.30, 4.70,
   3.27, 3.48 ,3.66  ,3.96,  4.30, 4.45, 5.16, 5.47, 5.53, 5.30, 4.70,
   3.22, 3.45 ,3.64  ,3.94,  4.29, 4.45, 5.16, 5.47, 5.53, 5.30, 4.70,
   3.07, 3.34 ,3.56  ,3.89,  4.26, 4.42, 5.15, 5.46, 5.52, 5.30, 4.70,
   2.72, 3.09 ,3.35  ,3.74,  4.16, 4.34, 5.13, 5.45, 5.51, 5.29, 4.68,
   2.24, 2.65 ,2.95  ,3.42,  3.92, 4.14, 5.06, 5.41, 5.48, 5.26, 4.64,
   1.74, 2.15 ,2.47  ,2.95,  3.49, 3.74, 4.86, 5.30, 5.39, 5.17, 4.53,
   1.24, 1.65 ,1.97  ,2.45,  3.00, 3.25, 4.47, 5.02, 5.16, 4.94, 4.27,
   0.742, 1.15 ,1.47  ,1.95,  2.50, 2.75, 3.98, 4.57, 4.73, 4.52, 3.84,
   0.242, 0.652,0.966 ,1.45,  2.00, 2.25, 3.48, 4.07, 4.24, 4.03, 3.35,
   -0.258, 0.152,0.466 ,0.95,	 1.50, 1.75, 2.98, 3.57, 3.74, 3.53, 2.85
   };

   const amrex::Real log_nhalf = LP2Di_(TCO_, NeffCO_, lenTCO_, iT0, iNeff0,
                                          nhalfCO_, T, log_NCOeff);
   const amrex::Real nhalf = pow(10, log_nhalf);

   return nhalf;

}

AMREX_GPU_HOST_DEVICE AMREX_INLINE void
actual_rhs(const burn_t &state, amrex::Array1D<amrex::Real, 1, neqs> &ydot) {

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

  // $JAFF REPEAT idx, rhs, cse IN rhses $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1] RADIATION True]$
  const amrex::Real cse$idx$ = $cse$;
  ydot($idx+1$) = $rhs$;
  // $JAFF END
  // $JAFF SUB nspec
  ydot($nspec+1$) /= state.rho;
  // $JAFF END
}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void
jac_chem(const burn_t &state, MatrixType &jac) {

}

template <class MatrixType>
AMREX_GPU_HOST_DEVICE AMREX_INLINE void actual_jac(const burn_t &state,
                                                   MatrixType &jac) {

  amrex::Array1D<amrex::Real, 0, NumSpec - 1> nden;
      for (int i = 0; i < NumSpec; ++i) {
      nden(i) = state.xn[i];
      }

  amrex::Real tgas = state.T;
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
  amrex::Real l0_co_interp1d = l0_co_interp1d_func(state);
  amrex::Real llte_co_interp2d = llte_co_interp2d_func(state, nden);
  amrex::Real psigd_coll_interp2d = psigd_coll_interp2d_func(state, nden);
  amrex::Real alpha_co_interp2d = alpha_co_interp2d_func(state, nden);
  amrex::Real nhalf_co_interp2d = nhalf_co_interp2d_func(state, nden);

  // $JAFF REPEAT idx, expr, cse IN jacobian $[REPLACE radeden\[\s*(\d+)\s*\] state.rn[\1] REPLACE photden\[\s*(\d+)\s*\] state.rn[\1] REPLACE rflux\[\s*(\d+)\s*\] state.rn[2*\1+1] REPLACE nden\[\s*(\d+)\s*\] state.xn[\1] RADIATION True USE_DEDT True]$
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
