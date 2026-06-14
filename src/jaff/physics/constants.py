# pyright: reportAttributeAccessIssue=false
"""Physical and astronomical constants as :class:`astropy.units.Quantity`.

This module is the single source of truth for physical constants in JAFF.
Every constant is an :class:`astropy.units.Quantity` carrying both a value and
a unit, sourced from :mod:`astropy.constants` (CODATA 2018) wherever astropy
ships it, and computed from those primitives otherwise.  Names match the
:mod:`astropy.constants` spelling (``k_B``, ``m_p``, ``M_sun``, ``N_A``, ``u``,
``R`` ...).

Unit systems
------------
The legacy ``cgs`` / ``si`` / ``gaussian`` / ``natural`` constant tables are
gone.  Because every constant is now a unit-aware ``Quantity``, the unit system
is selected *per quantity* at the call site:

>>> from jaff.physics import constants as c
>>> c.c.cgs  # speed of light in CGS
<Quantity 2.99792458e+10 cm / s>
>>> c.c.si  # ... in SI
<Quantity 2.99792458e+08 m / s>
>>> c.k_B.to("eV / K")  # ... in any explicit unit
<Quantity 8.617333e-05 eV / K>
>>> float(c.m_p.cgs.value)  # bare float when a number is required
1.67262192369e-24

The elementary charge keeps astropy's electromagnetic-unit views:

>>> c.e.esu  # Gaussian/CGS-ESU (Franklin)
<Quantity 4.8032047e-10 Fr>
>>> c.e.si  # SI (Coulomb)
<Quantity 1.60217663e-19 C>

Migration
---------
``constants.cgs.c``   ->  ``constants.c.cgs``
``constants.cgs.k_b`` ->  ``constants.k_B.cgs``  (astropy spelling)
``constants.cgs.ev_to_erg`` -> ``(1 * u.eV).to("erg")``  (trivial conversion)
"""

from __future__ import annotations

import astropy.constants as _ac
import astropy.units as _u

# =============================================================================
# Fundamental physical constants (astropy / CODATA 2018)
# =============================================================================
c = _ac.c
"""Speed of light in vacuum."""
h = _ac.h
"""Planck constant."""
hbar = _ac.hbar
"""Reduced Planck constant (h / 2pi)."""
G = _ac.G
"""Newtonian gravitational constant."""
k_B = _ac.k_B
"""Boltzmann constant."""
e = _ac.e
"""Elementary charge.  Use ``.esu`` (Gaussian/CGS) or ``.si`` (Coulomb)."""
m_e = _ac.m_e
"""Electron rest mass."""
m_p = _ac.m_p
"""Proton rest mass."""
m_n = _ac.m_n
"""Neutron rest mass."""
u = _ac.u
"""Atomic mass unit (1 u)."""
me_mp = (m_e / m_p).decompose()
"""Electron-to-proton mass ratio (dimensionless)."""

# =============================================================================
# Astronomical constants
# =============================================================================
M_sun = _ac.M_sun
"""Solar mass."""
R_sun = _ac.R_sun
"""Solar radius."""
L_sun = _ac.L_sun
"""Solar luminosity."""
pc = _ac.pc
"""Parsec."""
kpc = _ac.kpc
"""Kiloparsec."""
Mpc = 1.0 * _u.Mpc
"""Megaparsec."""
au = _ac.au
"""Astronomical unit."""
ly = 1.0 * _u.lyr
"""Light-year."""
H0 = 67.4 * _u.km / _u.s / _u.Mpc
"""Hubble constant (Planck 2018, 67.4 km/s/Mpc)."""

# =============================================================================
# Astrochemistry / radiation (computed from the primitives above)
# =============================================================================
sigma_sb = _ac.sigma_sb
"""Stefan-Boltzmann constant."""
a_rad = (4.0 * sigma_sb / c).to("erg / (cm3 K4)")
"""Radiation constant (a = 4 sigma / c)."""
alpha = _ac.alpha
"""Fine-structure constant (dimensionless, ~1/137)."""
sigma_T = _ac.sigma_T
"""Thomson scattering cross section."""
lambda_C = (h / (m_e * c)).to("cm")
"""Compton wavelength of the electron (h / m_e c)."""
a0 = _ac.a0
"""Bohr radius."""
Ry = (_ac.Ryd * h * c).to("eV")
"""Rydberg energy (~13.6 eV)."""
r_e = (alpha**2 * a0).to("cm")
"""Classical electron radius (alpha^2 * a0)."""
gyro_coeff = (e.esu / m_e).to("Fr / g")
"""Electron gyromagnetic coefficient (e / m_e) in CGS-ESU (Fr/g)."""

# =============================================================================
# Astrochemistry-specific constants
# =============================================================================
mu_H = m_p
"""Mean mass of a hydrogen atom (~proton mass)."""
mu_H2 = 2.0 * m_p
"""Mean mass of a hydrogen molecule (~2 proton masses)."""
nH_ref = (1.0 / m_p).to("1 / g")
"""Reference hydrogen number per unit mass (1 / m_p)."""

# =============================================================================
# Temperature
# =============================================================================
T_cmb = 2.725 * _u.K
"""CMB temperature."""
T_1ev = (1.0 * _u.eV / k_B).to("K")
"""Temperature equivalent of 1 eV (k_B T = 1 eV)."""

# =============================================================================
# Cross-section reference values
# =============================================================================
barn = 1.0 * _u.barn
"""1 barn (1e-24 cm^2)."""
mbarn = 1.0e6 * _u.barn
"""1 megabarn (1e6 barn)."""

# =============================================================================
# Reference
# =============================================================================
N_A = _ac.N_A
"""Avogadro constant."""
R = _ac.R
"""Molar gas constant (k_B * N_A)."""

__all__ = [
    "c",
    "h",
    "hbar",
    "G",
    "k_B",
    "e",
    "m_e",
    "m_p",
    "m_n",
    "u",
    "me_mp",
    "M_sun",
    "R_sun",
    "L_sun",
    "pc",
    "kpc",
    "Mpc",
    "au",
    "ly",
    "H0",
    "sigma_sb",
    "a_rad",
    "alpha",
    "sigma_T",
    "lambda_C",
    "a0",
    "Ry",
    "r_e",
    "gyro_coeff",
    "mu_H",
    "mu_H2",
    "nH_ref",
    "T_cmb",
    "T_1ev",
    "barn",
    "mbarn",
    "N_A",
    "R",
]
