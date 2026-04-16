# ABOUTME: Astrophysical constants in CGS units
# ABOUTME: Standard constants for chemical reaction network calculations


# =============================================================================
# Fundamental Physical Constants (CGS)
# =============================================================================

# Speed of light
c = 2.99792458e10  # cm/s

# Planck constant
h: float = 6.62607015e-27  # erg·s
h_bar: float = 1.054571817e-27  # erg·s

# Gravitational constant
G: float = 6.67430e-8  # cm³/(g·s²)

# Boltzmann constant
k_b: float = 1.380649e-16  # erg/K

# Elementary charge
e: float = 4.803204712570263e-10  # esu (statcoulomb)

# Electron mass
m_e: float = 9.1093837015e-28  # g

# Proton mass
m_p: float = 1.67262192369e-24  # g

# Neutron mass
m_n: float = 1.67492749804e-24  # g

# Atomic mass unit
amu: float = 1.66053906660e-24  # g

# Electron-to-proton mass ratio
me_mp: float = m_e / m_p  # dimensionless

# =============================================================================
# Astronomical Constants (CGS)
# =============================================================================

# Solar mass
m_sun: float = 1.98892e33  # g

# Solar radius
r_sun: float = 6.96e10  # cm

# Solar luminosity
l_sun: float = 3.828e33  # erg/s

# Parsec
pc: float = 3.086e18  # cm

# Kiloparsec
kpc: float = 1.0e3 * pc  # cm

# Megaparsec
mpc: float = 1.0e6 * pc  # cm

# Astronomical Unit
au: float = 1.495978707e13  # cm

# Light year
ly: float = 9.46073e17  # cm

# Hubble constant (current best estimate)
H0: float = 67.4e5  # cm/s/Mpc (using H0 = 67.4 km/s/Mpc)

# =============================================================================
# Physical Constants Used in Astrochemistry
# =============================================================================

# Stefan-Boltzmann constant
sigma_sb: float = 5.670374419e-5  # erg/(cm²·s·K⁴)

# Radiation constant (4*sigma_SB/c)
a_rad: float = 7.5657e-15  # erg/(cm³·K⁴)

# Fine structure constant
alpha: float = 7.2973525693e-3  # dimensionless

# Thomson cross section
sigma_T: float = 6.6524587e-25  # cm²

# Compton wavelength of electron
lambda_C: float = h / (m_e * c)  # cm

# Bohr radius
a0: float = 0.5291772e-8  # cm

# Rydberg constant (times hc)
Ry_hc: float = 2.1798723611e-11  # erg

# Rydberg energy
Ry: float = 13.605693  # eV (for reference, ~2.1799e-11 erg)

# =============================================================================
# Physical Constants for Gas/Plasma Astrophysics
# =============================================================================

# Classical electron radius
r_e: float = e**2 / (m_e * c**2)  # cm

# Cyclotron frequency coefficient (e*B/(m_e*c))
gyro_coeff: float = 1.758820024e7  # Hz/Gauss

# =============================================================================
# Conversion Factors and Derived Constants
# =============================================================================

# Electrovolts to erg
ev_to_erg: float = 1.602176634e-12  # erg/eV

# Mean molecular weight (for atomic hydrogen)
mu_H: float = m_p  # g (hydrogen nucleus)

# Mean molecular weight (for H2)
mu_H2: float = 2.0 * m_p  # g

# Dimensionless Boltzmann constant for convenience
kb_ev: float = k_b / ev_to_erg  # eV/K

# =============================================================================
# Temperature-related Constants
# =============================================================================

# Cosmic microwave background temperature
T_cmb: float = 2.725  # K

# Temperature corresponding to 1 eV
T_1ev: float = ev_to_erg / k_b  # K (~11604.52 K)

# =============================================================================
# Density-related Constants
# =============================================================================

# Number density corresponding to 1 g/cm³ of hydrogen
nH_ref: float = 1.0 / m_p  # cm⁻³

# =============================================================================
# Cross section reference values
# =============================================================================

# Barn (common unit for microscopic cross sections)
barn: float = 1.0e-24  # cm²

# Megabarn
mbarn: float = 1.0e6 * barn  # cm²

# =============================================================================
# Physical Constants for Reference
# =============================================================================

# Avogadro's number (for reference)
n_A: float = 6.02214076e23  # dimensionless

# Gas constant (for reference)
R_gas: float = k_b * n_A  # erg/(mol·K)

# =============================================================================
# Notes on CGS Units
# =============================================================================
# CGS-Gaussian (CGS-ESU) system used:
# - Length: centimeter (cm)
# - Mass: gram (g)
# - Time: second (s)
# - Energy: erg (1 erg = 1 g·cm²/s²)
# - Temperature: Kelvin (K)
# - Charge: esu (statcoulomb)
# - Magnetic field: Gauss
#
# Key differences from SI:
# - Speed of light not in fundamental equations
# - Charge has different units (esu vs Coulomb)
# - 4π factors appear differently in Maxwell's equations
# - No μ₀ and ε₀, instead uses c explicitly
#
# For practical calculations in astrochemistry:
# - Use constants as defined here for reaction rates
# - Temperature in Kelvin (not CGS time units)
# - Densities in particles/cm³
# - Cross sections in cm²
# - Energies in erg or eV (with conversion factor)
