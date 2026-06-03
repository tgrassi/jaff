# ABOUTME: Unit tests for the jaff.physics units module
# ABOUTME: Tests convert(), Quantity, bridges, errors, and constant-drift guards

import numpy as np
import pytest

from jaff.errors import IncompatibleUnitsError, UnknownUnitError
from jaff.physics import units
from jaff.physics.constants import cgs
from jaff.physics._units import (
    _UNITS,
    Dimension,
    Quantity,
    convert,
)


class TestWithinDimension:
    """Pure factor-ratio conversions inside a single dimension."""

    @pytest.mark.parametrize("name", list(_UNITS))
    def test_roundtrip_scalar(self, name):
        base = _base_unit(_UNITS[name].dimension)
        assert convert(convert(3.0, base, name), name, base) == pytest.approx(3.0)

    @pytest.mark.parametrize("name", list(_UNITS))
    def test_roundtrip_array(self, name):
        base = _base_unit(_UNITS[name].dimension)
        x = np.array([1.0, 2.5, 7.0])
        out = convert(convert(x, base, name), name, base)
        assert isinstance(out, np.ndarray)
        np.testing.assert_allclose(out, x)

    def test_known_energy(self):
        assert convert(13.605693, "eV", "Ry") == pytest.approx(1.0)
        assert convert(1.0, "Ry", "eV") == pytest.approx(13.605693, rel=1e-6)
        assert convert(1.0, "keV", "eV") == pytest.approx(1000.0)
        assert convert(1.0, "MeV", "eV") == pytest.approx(1e6)
        assert convert(1.0, "J", "erg") == pytest.approx(1e7)

    def test_known_length(self):
        assert convert(1.0, "nm", "angstrom") == pytest.approx(10.0)
        assert convert(1.0, "um", "nm") == pytest.approx(1000.0)
        assert convert(1.0, "nm", "cm") == pytest.approx(1e-7)

    def test_known_area(self):
        assert convert(1.0, "Mb", "cm2") == pytest.approx(1e-18)
        assert convert(1.0, "barn", "cm2") == pytest.approx(1e-24)
        assert convert(1.0, "Mb", "barn") == pytest.approx(1e6)

    def test_known_time(self):
        assert convert(1.0, "ms", "s") == pytest.approx(1e-3)
        assert convert(1.0, "us", "ns") == pytest.approx(1000.0)

    def test_known_mass(self):
        assert convert(1.0, "amu", "g") == pytest.approx(cgs.amu)
        assert convert(1.0, "m_p", "g") == pytest.approx(cgs.m_p)
        assert convert(1.0, "kg", "g") == pytest.approx(1000.0)

    def test_known_charge(self):
        assert convert(1.0, "C", "esu") == pytest.approx(cgs.c / 10.0)
        assert convert(1.0, "statC", "esu") == pytest.approx(1.0)


class TestBridges:
    """Cross-dimension conversions through physics bridges."""

    def test_wavelength_to_energy_lyman_alpha(self):
        # Lyman-alpha 121.567 nm ~ 10.199 eV
        assert convert(121.567, "nm", "eV") == pytest.approx(10.199, rel=1e-3)

    def test_energy_to_wavelength_rydberg_limit(self):
        # 1 Ry ~ 91.18 nm (Lyman limit)
        assert convert(1.0, "Ry", "nm") == pytest.approx(91.18, rel=1e-3)

    def test_wavelength_roundtrip(self):
        assert convert(convert(121.6, "nm", "eV"), "eV", "nm") == pytest.approx(121.6)

    def test_temperature_to_energy(self):
        assert convert(1.0, "eV", "K") == pytest.approx(cgs.T_1ev, rel=1e-6)
        assert convert(cgs.T_1ev, "K", "eV") == pytest.approx(1.0, rel=1e-6)
        assert convert(1.0, "K", "eV") == pytest.approx(cgs.kb_ev, rel=1e-6)

    def test_frequency_to_energy(self):
        assert convert(1.0, "Hz", "erg") == pytest.approx(cgs.h)
        assert convert(convert(5.0, "Hz", "erg"), "erg", "Hz") == pytest.approx(5.0)

    def test_bridge_array(self):
        out = convert(np.array([121.567, 91.18]), "nm", "eV")
        assert isinstance(out, np.ndarray)
        np.testing.assert_allclose(out, [10.199, 13.598], rtol=1e-3)


class TestListInput:
    """convert() and Quantity accept python lists/tuples elementwise."""

    def test_convert_list_factor(self):
        out = convert([1.0, 2.0, 3.0], "keV", "eV")
        assert isinstance(out, np.ndarray)
        np.testing.assert_allclose(out, [1000.0, 2000.0, 3000.0])

    def test_convert_tuple_bridge(self):
        out = convert((121.567, 91.18), "nm", "eV")
        assert isinstance(out, np.ndarray)
        np.testing.assert_allclose(out, [10.199, 13.598], rtol=1e-3)

    def test_quantity_list(self):
        q = Quantity([1.0, 2.0], "keV")
        assert isinstance(q.value, np.ndarray)
        np.testing.assert_allclose(q.eV, [1000.0, 2000.0])

    def test_scalar_stays_float(self):
        assert isinstance(convert(2.0, "keV", "eV"), float)


class TestQuantity:
    def test_attribute_access(self):
        assert Quantity(121.6, "nm").eV == pytest.approx(10.2, rel=1e-2)
        assert Quantity(1.0, "eV").erg == pytest.approx(cgs.ev_to_erg)

    def test_to(self):
        assert Quantity(1.0, "eV").to("Ry").value == pytest.approx(
            1.0 / 13.605693, rel=1e-6
        )
        assert Quantity(1.0, "nm").to("angstrom").value == pytest.approx(10.0)

    def test_props(self):
        q = Quantity(1.0, "eV")
        assert q.unit == "eV"
        assert q.dimension is Dimension.ENERGY

    def test_add_sub(self):
        assert (Quantity(1.0, "eV") + Quantity(1.0, "keV")).eV == pytest.approx(1001.0)
        assert (Quantity(2.0, "keV") - Quantity(1000.0, "eV")).keV == pytest.approx(1.0)

    def test_scalar_mul_div(self):
        assert (Quantity(2.0, "eV") * 3).value == pytest.approx(6.0)
        assert (3 * Quantity(2.0, "eV")).value == pytest.approx(6.0)
        assert (Quantity(6.0, "eV") / 2).value == pytest.approx(3.0)

    def test_quantity_ratio_dimensionless(self):
        assert Quantity(6.0, "eV") / Quantity(2.0, "eV") == pytest.approx(3.0)
        assert Quantity(1.0, "keV") / Quantity(1.0, "eV") == pytest.approx(1000.0)

    def test_neg(self):
        assert (-Quantity(5.0, "eV")).value == pytest.approx(-5.0)

    def test_comparison(self):
        assert Quantity(1.0, "keV") > Quantity(1.0, "eV")
        assert Quantity(1000.0, "eV") == Quantity(1.0, "keV")

    def test_dir_lists_units(self):
        d = dir(Quantity(1.0, "eV"))
        assert "eV" in d and "nm" in d

    def test_not_hashable(self):
        with pytest.raises(TypeError):
            {Quantity(1.0, "eV")}


class TestErrors:
    def test_incompatible_convert(self):
        with pytest.raises(IncompatibleUnitsError):
            convert(1.0, "eV", "cm2")

    def test_unknown_unit(self):
        with pytest.raises(UnknownUnitError):
            convert(1.0, "foo", "eV")
        with pytest.raises(UnknownUnitError):
            Quantity(1.0, "foo")

    def test_incompatible_add(self):
        with pytest.raises(IncompatibleUnitsError):
            Quantity(1.0, "eV") + Quantity(1.0, "cm")

    def test_bad_attribute(self):
        with pytest.raises(AttributeError):
            Quantity(1.0, "eV").nonsense

    def test_quantity_product_unsupported(self):
        with pytest.raises(TypeError):
            Quantity(1.0, "eV") * Quantity(1.0, "eV")  # ty: ignore[unsupported-operator]


class TestConstantDrift:
    """Guard against duplicated magic numbers drifting from constants.cgs."""

    def test_factors_match_constants(self):
        assert _UNITS["eV"].factor == cgs.ev_to_erg
        assert _UNITS["Mb"].factor == cgs.mbarn
        assert _UNITS["barn"].factor == cgs.barn
        assert _UNITS["Ry"].factor == cgs.Ry_hc
        assert _UNITS["amu"].factor == cgs.amu


class TestModuleApi:
    def test_exposed_via_physics_units(self):
        assert units.convert(1.0, "keV", "eV") == pytest.approx(1000.0)
        assert units.Quantity(1.0, "eV").unit == "eV"


def _base_unit(dim: Dimension) -> str:
    """Return the registry's base-unit name (factor == 1) for a dimension."""
    for name, u in _UNITS.items():
        if u.dimension is dim and u.factor == 1.0:
            return name
    raise AssertionError(f"no base unit for {dim}")
