# ABOUTME: Physical constants in multiple unit systems
# ABOUTME: CGS, SI, Gaussian, and natural units for astrochemistry and particle physics

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    """Physical and astronomical constants in consistent unit systems."""

    # Fundamental Physical Constants
    c: float  # speed of light
    h: float  # Planck constant
    h_bar: float  # reduced Planck constant
    G: float  # gravitational constant
    k_b: float  # Boltzmann constant
    e: float  # elementary charge
    m_e: float  # electron mass
    m_p: float  # proton mass
    m_n: float  # neutron mass
    amu: float  # atomic mass unit
    me_mp: float  # electron-to-proton mass ratio

    # Astronomical Constants
    m_sun: float  # solar mass
    r_sun: float  # solar radius
    l_sun: float  # solar luminosity
    pc: float  # parsec
    kpc: float  # kiloparsec
    mpc: float  # megaparsec
    au: float  # astronomical unit
    ly: float  # light year
    H0: float  # Hubble constant

    # Physical Constants Used in Astrochemistry
    sigma_sb: float  # Stefan-Boltzmann constant
    a_rad: float  # radiation constant
    alpha: float  # fine structure constant
    sigma_T: float  # Thomson cross section
    lambda_C: float  # Compton wavelength of electron
    a0: float  # Bohr radius
    Ry_hc: float  # Rydberg constant times hc
    Ry: float  # Rydberg energy

    # Physical Constants for Gas/Plasma Astrophysics
    r_e: float  # classical electron radius
    gyro_coeff: float  # cyclotron frequency coefficient

    # Conversion Factors and Derived Constants
    ev_to_erg: float  # electrovolts to energy conversion
    mu_H: float  # mean molecular weight (atomic hydrogen)
    mu_H2: float  # mean molecular weight (H2)
    kb_ev: float  # Boltzmann constant in eV/K

    # Temperature-related Constants
    T_cmb: float  # cosmic microwave background temperature
    T_1ev: float  # temperature corresponding to 1 eV

    # Density-related Constants
    nH_ref: float  # reference hydrogen number density

    # Cross section reference values
    barn: float  # barn unit
    mbarn: float  # megabarn unit

    # Physical Constants for Reference
    n_A: float  # Avogadro's number
    R_gas: float  # gas constant


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
# Unit Systems Documentation
# =============================================================================
"""
UNIT SYSTEMS
=============

CGS-ESU (cgs_esu / cgs):
    Length: centimeter (cm)
    Mass: gram (g)
    Time: second (s)
    Energy: erg (1 erg = 1 g·cm²/s²)
    Temperature: Kelvin (K)
    Charge: esu (electrostatic unit / statcoulomb)
    Magnetic field: stattesla
    Pure electrostatic CGS system

SI (si):
    Length: meter (m)
    Mass: kilogram (kg)
    Time: second (s)
    Energy: joule (J = kg·m²/s²)
    Temperature: Kelvin (K)
    Charge: coulomb (C)
    Magnetic field: tesla (T)
    International standard, common in modern physics

Gaussian (gaussian):
    Length: centimeter (cm)
    Mass: gram (g)
    Time: second (s)
    Energy: erg
    Temperature: Kelvin (K)
    Charge: esu
    Magnetic field: Gauss
    Standard in astrophysics and plasma physics.
    Combines ESU for charge/electric fields and EMU for magnetic fields.
    Factors of c appear explicitly in Maxwell's equations.

Natural Units (natural):
    ℏ = c = 1 (dimensionless)
    Energy scale: MeV (can be rescaled to GeV, etc.)
    Length: MeV⁻¹ (≈ 1.973 × 10⁻¹⁴ cm = 1 fm)
    Time: MeV⁻¹ (≈ 6.583 × 10⁻²² s)
    Mass: MeV
    Temperature: Kelvin (K), with k_B = 8.617 × 10⁻¹¹ MeV/K
    Convenient for particle physics and quantum mechanics calculations
    Common in high-energy physics and relativistic calculations

USAGE:
    from jaff.physics.constants import cgs, si, gaussian, natural

    # Access constants via dot notation
    c_cgs = cgs.c        # 2.998e10 cm/s
    c_si = si.c          # 2.998e8 m/s
    m_e_natural = natural.m_e  # 0.511 MeV

KEY CONVERSIONS:
    1 MeV⁻¹ = 1.973 × 10⁻¹⁴ cm (natural to CGS)
    1 fm = 197.327 MeV⁻¹ (CGS to natural)
    α ≈ 1/137 (fine structure constant, dimensionless in all systems)
    ℏc ≈ 197.327 MeV·fm

WHEN TO USE EACH SYSTEM:
    - CGS: Astrophysics, plasma physics, older literature
    - SI: Modern physics, engineering, international standards
    - Gaussian: Electromagnetism in CGS framework, theoretical physics
    - Natural: Particle physics, quantum field theory, relativistic calculations
"""
