"""
Physical and astronomical constants for multiple unit systems.

This module defines the :class:`Constants` dataclass and provides four
pre-instantiated constant sets:

- ``cgs`` -- CGS-ESU (centimetre–gram–second, electrostatic units). This is
  the primary system used throughout JAFF for internal calculations.
- ``si`` -- SI (metre–kilogram–second).
- ``gaussian`` -- Gaussian CGS (combines ESU for electric quantities and EMU
  for magnetic quantities; factors of *c* appear explicitly in Maxwell's
  equations).
- ``natural`` -- Natural units with ℏ = c = 1, energies in MeV.

All constant values follow CODATA 2018 recommended values where applicable.

Examples
--------
>>> from jaff.physics.constants import cgs, si
>>> cgs.c  # speed of light in cm/s
2.99792458e+10
>>> si.k_b  # Boltzmann constant in J/K
1.380649e-23
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    """
    Immutable container for physical and astronomical constants.

    All fields are floats whose numeric values correspond to a specific unit
    system (CGS, SI, Gaussian, or natural units).  The dataclass is frozen so
    that constants cannot be accidentally mutated at runtime.

    Parameters
    ----------
    c : float
        Speed of light in vacuum.
    h : float
        Planck constant.
    h_bar : float
        Reduced Planck constant (ℏ = h / 2π).
    G : float
        Newtonian gravitational constant.
    k_b : float
        Boltzmann constant.
    e : float
        Elementary charge (esu in CGS/Gaussian; coulombs in SI; dimensionless
        coupling √α in natural units).
    m_e : float
        Electron rest mass.
    m_p : float
        Proton rest mass.
    m_n : float
        Neutron rest mass.
    amu : float
        Atomic mass unit (1 u).
    me_mp : float
        Electron-to-proton mass ratio (dimensionless).
    m_sun : float
        Solar mass.
    r_sun : float
        Solar radius.
    l_sun : float
        Solar luminosity.
    pc : float
        Parsec.
    kpc : float
        Kiloparsec.
    mpc : float
        Megaparsec.
    au : float
        Astronomical unit.
    ly : float
        Light-year.
    H0 : float
        Hubble constant (67.4 km/s/Mpc expressed in the unit system's
        velocity and distance units).
    sigma_sb : float
        Stefan–Boltzmann constant.
    a_rad : float
        Radiation constant (a = 4σ/c).
    alpha : float
        Fine-structure constant (dimensionless, ≈ 1/137).
    sigma_T : float
        Thomson scattering cross section.
    lambda_C : float
        Compton wavelength of the electron (h / m_e c).
    a0 : float
        Bohr radius.
    Ry_hc : float
        Rydberg energy (1 Ry = 13.6 eV expressed in the unit system's energy
        units).
    Ry : float
        Rydberg energy in electronvolts (always 13.605693 eV, unit-independent).
    r_e : float
        Classical electron radius.
    gyro_coeff : float
        Gyration-frequency coefficient (charge/mass, or equivalent).
    ev_to_erg : float
        Conversion factor: 1 eV expressed in the unit system's energy unit.
    mu_H : float
        Mean mass of a hydrogen atom (≈ proton mass).
    mu_H2 : float
        Mean mass of a hydrogen molecule (≈ 2 × proton mass).
    kb_ev : float
        Boltzmann constant in eV/K (useful for converting temperatures).
    T_cmb : float
        CMB temperature in Kelvin (2.725 K; system-independent).
    T_1ev : float
        Temperature equivalent of 1 eV (k_B T = 1 eV ⟹ T in Kelvin).
    nH_ref : float
        Reference hydrogen number density corresponding to 1 hydrogen atom
        per unit volume of the system.
    barn : float
        1 barn expressed in the unit system's area unit (10⁻²⁴ cm²).
    mbarn : float
        1 megabarn expressed in the unit system's area unit.
    n_A : float
        Avogadro constant (dimensionless, same in all systems).
    R_gas : float
        Molar gas constant (k_B × N_A).

    Notes
    -----
    The dataclass is declared ``frozen=True`` to make instances hashable and
    prevent accidental mutation.  Use the module-level instances ``cgs``,
    ``si``, ``gaussian``, and ``natural`` rather than constructing your own.
    """

    # Fundamental Physical Constants
    c: float
    h: float
    h_bar: float
    G: float
    k_b: float
    e: float
    m_e: float
    m_p: float
    m_n: float
    amu: float
    me_mp: float

    # Astronomical Constants
    m_sun: float
    r_sun: float
    l_sun: float
    pc: float
    kpc: float
    mpc: float
    au: float
    ly: float
    H0: float

    # Astrochemistry
    sigma_sb: float
    a_rad: float
    alpha: float
    sigma_T: float
    lambda_C: float
    a0: float
    Ry_hc: float
    Ry: float

    # Gas/Plasma Astrophysics
    r_e: float
    gyro_coeff: float

    # Conversion Factors and Derived Constants
    ev_to_erg: float
    mu_H: float
    mu_H2: float
    kb_ev: float

    # Temperature
    T_cmb: float
    T_1ev: float

    # Density
    nH_ref: float

    # Cross section reference values
    barn: float
    mbarn: float

    # Reference
    n_A: float
    R_gas: float


# =============================================================================
# CGS-ESU Units
# =============================================================================
# Length: cm, Mass: g, Time: s, Energy: erg, Temperature: K
# Charge: esu, Magnetic field: stattesla
cgs = Constants(
    # Fundamental Physical Constants (CGS)
    c=2.99792458e10,  # cm/s
    h=6.62607015e-27,  # erg·s
    h_bar=1.054571817e-27,  # erg·s
    G=6.67430e-8,  # cm³/(g·s²)
    k_b=1.380649e-16,  # erg/K
    e=4.803204712570263e-10,  # esu
    m_e=9.1093837015e-28,  # g
    m_p=1.67262192369e-24,  # g
    m_n=1.67492749804e-24,  # g
    amu=1.66053906660e-24,  # g
    me_mp=9.1093837015e-28 / 1.67262192369e-24,  # dimensionless
    # Astronomical Constants (CGS)
    m_sun=1.98892e33,  # g
    r_sun=6.96e10,  # cm
    l_sun=3.828e33,  # erg/s
    pc=3.086e18,  # cm
    kpc=3.086e21,  # cm
    mpc=3.086e24,  # cm
    au=1.495978707e13,  # cm
    ly=9.46073e17,  # cm
    H0=67.4e5,  # cm/s/Mpc
    # Physical Constants Used in Astrochemistry (CGS)
    sigma_sb=5.670374419e-5,  # erg/(cm²·s·K⁴)
    a_rad=7.5657e-15,  # erg/(cm³·K⁴)
    alpha=7.2973525693e-3,  # dimensionless
    sigma_T=6.6524587e-25,  # cm²
    lambda_C=6.62607015e-27 / (9.1093837015e-28 * 2.99792458e10),  # cm
    a0=0.5291772e-8,  # cm
    Ry_hc=2.1798723611e-11,  # erg
    Ry=13.605693,  # eV
    # Physical Constants for Gas/Plasma Astrophysics (CGS-ESU)
    r_e=(4.803204712570263e-10) ** 2 / (9.1093837015e-28 * (2.99792458e10) ** 2),  # cm
    gyro_coeff=4.803204712570263e-10 / 9.1093837015e-28,  # (rad/s)/stattesla
    # Conversion Factors and Derived Constants (CGS-ESU)
    ev_to_erg=1.602176634e-12,  # erg/eV
    mu_H=1.67262192369e-24,  # g
    mu_H2=2.0 * 1.67262192369e-24,  # g
    kb_ev=1.380649e-16 / 1.602176634e-12,  # eV/K
    # Temperature-related Constants
    T_cmb=2.725,  # K
    T_1ev=1.602176634e-12 / 1.380649e-16,  # K
    # Density-related Constants
    nH_ref=1.0 / 1.67262192369e-24,  # cm⁻³
    # Cross section reference values
    barn=1.0e-24,  # cm²
    mbarn=1.0e6 * 1.0e-24,  # cm²
    # Physical Constants for Reference
    n_A=6.02214076e23,  # dimensionless
    R_gas=1.380649e-16 * 6.02214076e23,  # erg/(mol·K)
)


# =============================================================================
# SI Units
# =============================================================================
# Length: m, Mass: kg, Time: s, Energy: J, Temperature: K
# Charge: C, Magnetic field: T
si = Constants(
    # Fundamental Physical Constants (SI)
    c=2.99792458e8,  # m/s
    h=6.62607015e-34,  # J·s
    h_bar=1.054571817e-34,  # J·s
    G=6.67430e-11,  # m³/(kg·s²)
    k_b=1.380649e-23,  # J/K
    e=1.602176634e-19,  # C
    m_e=9.1093837015e-31,  # kg
    m_p=1.67262192369e-27,  # kg
    m_n=1.67492749804e-27,  # kg
    amu=1.66053906660e-27,  # kg
    me_mp=9.1093837015e-31 / 1.67262192369e-27,  # dimensionless
    # Astronomical Constants (SI)
    m_sun=1.98892e30,  # kg
    r_sun=6.96e8,  # m
    l_sun=3.828e26,  # W
    pc=3.086e16,  # m
    kpc=3.086e19,  # m
    mpc=3.086e22,  # m
    au=1.495978707e11,  # m
    ly=9.46073e15,  # m
    H0=67.4e3,  # m/s/Mpc (67.4 km/s/Mpc)
    # Physical Constants Used in Astrochemistry (SI)
    sigma_sb=5.670374419e-8,  # W/(m²·K⁴)
    a_rad=7.5657e-16,  # J/(m³·K⁴)
    alpha=7.2973525693e-3,  # dimensionless
    sigma_T=6.6524587e-29,  # m²
    lambda_C=6.62607015e-34 / (9.1093837015e-31 * 2.99792458e8),  # m
    a0=0.5291772e-10,  # m
    Ry_hc=2.1798723611e-18,  # J
    Ry=13.605693,  # eV
    # Physical Constants for Gas/Plasma Astrophysics (SI)
    r_e=(1.602176634e-19) ** 2
    / (9.1093837015e-31 * (2.99792458e8) ** 2 * 8.8541878128e-12),  # m
    gyro_coeff=1.758820024e11,  # Hz/T
    # Conversion Factors and Derived Constants (SI)
    ev_to_erg=1.602176634e-19,  # J/eV
    mu_H=1.67262192369e-27,  # kg
    mu_H2=2.0 * 1.67262192369e-27,  # kg
    kb_ev=1.380649e-23 / 1.602176634e-19,  # eV/K
    # Temperature-related Constants
    T_cmb=2.725,  # K
    T_1ev=1.602176634e-19 / 1.380649e-23,  # K
    # Density-related Constants
    nH_ref=1.0 / 1.67262192369e-27,  # m⁻³
    # Cross section reference values
    barn=1.0e-28,  # m²
    mbarn=1.0e6 * 1.0e-28,  # m²
    # Physical Constants for Reference
    n_A=6.02214076e23,  # dimensionless
    R_gas=1.380649e-23 * 6.02214076e23,  # J/(mol·K)
)


# =============================================================================
# Gaussian Units
# =============================================================================
# Length: cm, Mass: g, Time: s, Energy: erg
# Charge: esu, Magnetic field: stattesla
# c appears explicitly in Maxwell's equations and Lorentz force
gaussian = Constants(
    # Fundamental Physical Constants (Gaussian)
    c=2.99792458e10,  # cm/s
    h=6.62607015e-27,  # erg·s
    h_bar=1.054571817e-27,  # erg·s
    G=6.67430e-8,  # cm³/(g·s²)
    k_b=1.380649e-16,  # erg/K
    e=4.803204712570263e-10,  # esu
    m_e=9.1093837015e-28,  # g
    m_p=1.67262192369e-24,  # g
    m_n=1.67492749804e-24,  # g
    amu=1.66053906660e-24,  # g
    me_mp=9.1093837015e-28 / 1.67262192369e-24,  # dimensionless
    # Astronomical Constants (Gaussian)
    m_sun=1.98892e33,  # g
    r_sun=6.96e10,  # cm
    l_sun=3.828e33,  # erg/s
    pc=3.086e18,  # cm
    kpc=3.086e21,  # cm
    mpc=3.086e24,  # cm
    au=1.495978707e13,  # cm
    ly=9.46073e17,  # cm
    H0=67.4e5,  # cm/s/Mpc
    # Physical Constants Used in Astrochemistry (Gaussian)
    sigma_sb=5.670374419e-5,  # erg/(cm²·s·K⁴)
    a_rad=7.5657e-15,  # erg/(cm³·K⁴)
    alpha=7.2973525693e-3,  # dimensionless
    sigma_T=6.6524587e-25,  # cm²
    lambda_C=6.62607015e-27 / (9.1093837015e-28 * 2.99792458e10),  # cm
    a0=0.5291772e-8,  # cm
    Ry_hc=2.1798723611e-11,  # erg
    Ry=13.605693,  # eV
    # Physical Constants for Gas/Plasma Astrophysics (Gaussian)
    r_e=(4.803204712570263e-10) ** 2 / (9.1093837015e-28 * (2.99792458e10) ** 2),  # cm
    gyro_coeff=1.758820024e7,  # Hz/Gauss
    # Conversion Factors and Derived Constants (Gaussian)
    ev_to_erg=1.602176634e-12,  # erg/eV
    mu_H=1.67262192369e-24,  # g
    mu_H2=2.0 * 1.67262192369e-24,  # g
    kb_ev=1.380649e-16 / 1.602176634e-12,  # eV/K
    # Temperature-related Constants
    T_cmb=2.725,  # K
    T_1ev=1.602176634e-12 / 1.380649e-16,  # K
    # Density-related Constants
    nH_ref=1.0 / 1.67262192369e-24,  # cm⁻³
    # Cross section reference values
    barn=1.0e-24,  # cm²
    mbarn=1.0e6 * 1.0e-24,  # cm²
    # Physical Constants for Reference
    n_A=6.02214076e23,  # dimensionless
    R_gas=1.380649e-16 * 6.02214076e23,  # erg/(mol·K)
)


# =============================================================================
# Natural Units
# =============================================================================
# ℏ = c = 1 (dimensionless). Energy scale: MeV
# Length: MeV⁻¹ (fm), Time: MeV⁻¹ (ℏ/MeV), Energy: MeV, Mass: MeV
# Note: Temperature in Kelvin, but k_B appears as 8.617 × 10⁻¹¹ MeV/K
# Conversion: 1 MeV⁻¹ ≈ 1.973 × 10⁻¹⁴ cm, 1 fm ≈ 5.068 MeV⁻¹
natural = Constants(
    # Fundamental Physical Constants (Natural units, ℏ = c = 1)
    c=1.0,  # dimensionless
    h=2.0 * 3.14159265359,  # dimensionless (h = 2π in natural units)
    h_bar=1.0,  # dimensionless
    G=6.70883e-39,  # MeV⁻² (Newton's constant in natural units)
    k_b=8.617333262e-11,  # MeV/K
    e=0.30282212088,  # dimensionless (fine structure constant: α ≈ 1/137)
    m_e=0.51099895000,  # MeV
    m_p=938.27208816,  # MeV
    m_n=939.56542052,  # MeV
    amu=931.49410242,  # MeV
    me_mp=0.51099895000 / 938.27208816,  # dimensionless
    # Astronomical Constants (Natural units)
    m_sun=1.98892e33 * 1.78266192e-24,  # MeV (1 g ≈ 5.609 × 10²⁶ MeV)
    r_sun=6.96e10 * 5.0677309e13,  # MeV⁻¹ (1 cm ≈ 5.068 × 10¹³ MeV⁻¹)
    l_sun=3.828e33 * 1.602176634e-6,  # MeV (erg to MeV conversion)
    pc=3.086e18 * 5.0677309e13,  # MeV⁻¹
    kpc=3.086e21 * 5.0677309e13,  # MeV⁻¹
    mpc=3.086e24 * 5.0677309e13,  # MeV⁻¹
    au=1.495978707e13 * 5.0677309e13,  # MeV⁻¹
    ly=9.46073e17 * 5.0677309e13,  # MeV⁻¹
    H0=67.4e5 / (3.086e19) * 1.973269804e-14 * 1e-6,  # Mpc⁻¹ in natural units
    # Physical Constants Used in Astrochemistry (Natural)
    sigma_sb=5.670374419e-5 * 1.602176634e-6 / ((2.99792458e10) ** 3),  # MeV⁻² K⁻⁴
    a_rad=7.5657e-15 * 1.602176634e-6 / ((2.99792458e10) ** 3),  # MeV K⁻⁴
    alpha=7.2973525693e-3,  # dimensionless (fine structure constant)
    sigma_T=6.6524587e-25 * (5.0677309e13) ** 2,  # MeV⁻²
    lambda_C=1.973269804e-14,  # MeV⁻¹ (2π/m_e in natural units)
    a0=0.5291772e-8 * 5.0677309e13,  # MeV⁻¹
    Ry_hc=13.605693 * 1e-3,  # MeV (Rydberg in natural units)
    Ry=13.605693,  # eV
    # Physical Constants for Gas/Plasma Astrophysics (Natural)
    r_e=2.818e-15 * 5.0677309e13,  # MeV⁻¹ (classical electron radius)
    gyro_coeff=1.758820024e7
    * (2.99792458e10)
    / (4.803204712570263e-10),  # Hz/Gauss in natural
    # Conversion Factors and Derived Constants (Natural)
    ev_to_erg=1.602176634e-12 * 1e-6,  # MeV (1 eV = 1e-6 MeV in natural units)
    mu_H=938.27208816,  # MeV (proton mass in natural units)
    mu_H2=2.0 * 938.27208816,  # MeV (H2 mass in natural units)
    kb_ev=8.617333262e-5,  # eV/K (Boltzmann constant)
    # Temperature-related Constants
    T_cmb=2.725,  # K
    T_1ev=11604.52,  # K (temperature for 1 eV)
    # Density-related Constants
    nH_ref=(5.0677309e13) ** 3,  # MeV³ (1 g/cm³ hydrogen in natural units)
    # Cross section reference values
    barn=1.0e-24 * (5.0677309e13) ** 2,  # MeV⁻²
    mbarn=1.0e6 * 1.0e-24 * (5.0677309e13) ** 2,  # MeV⁻²
    # Physical Constants for Reference
    n_A=6.02214076e23,  # dimensionless
    R_gas=8.617333262e-11 * 6.02214076e23,  # MeV/K
)


# =============================================================================
# Unit Systems Quick-Reference
# =============================================================================
# CGS-ESU (cgs):  cm, g, s, erg, K, esu, stattesla
# SI (si):        m, kg, s, J, K, C, T
# Gaussian:       cm, g, s, erg, K, esu, Gauss  (c explicit in Maxwell eqs)
# Natural:        ℏ = c = 1; energy in MeV; length in MeV⁻¹ ≈ 1.973×10⁻¹⁴ cm
#
# Key cross-system conversions:
#   1 MeV⁻¹ = 1.973×10⁻¹⁴ cm   (natural → CGS length)
#   1 fm    = 5.068 MeV⁻¹        (CGS → natural length)
#   ℏc      ≈ 197.327 MeV·fm
#   α       ≈ 1/137 (fine-structure constant, dimensionless in all systems)
#
# Preferred system per domain:
#   Astrochemistry / plasma physics : CGS or Gaussian
#   Modern physics / engineering    : SI
#   Particle / quantum field theory : Natural
