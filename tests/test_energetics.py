import pytest

from almgsi_dft.energetics import (
    chemical_potential,
    check_compatible,
    ev_to_ry,
    pair_binding_energy,
    require_reference,
    ry_to_ev,
    substitution_formation_energy,
)
from almgsi_dft.exceptions import IncompatibleCalculationError


def test_conversions_roundtrip():
    assert ev_to_ry(ry_to_ev(2.0)) == pytest.approx(2.0)


def test_formation_energy_formula_synthetic():
    assert substitution_formation_energy(-100.0, -95.0, -3.0, -2.0) == pytest.approx(-6.0)


def test_pair_binding_sign_convention_synthetic():
    assert pair_binding_energy(-101.0, -102.0, -205.0, -1.0) == pytest.approx(3.0)


def test_mu_requires_atoms():
    with pytest.raises(ValueError):
        chemical_potential(1.0, 0)


def test_missing_reference_error():
    with pytest.raises(KeyError):
        require_reference({}, "Al32")


def test_incompatible_calculation_error():
    with pytest.raises(IncompatibleCalculationError):
        check_compatible([{"ecutwfc_ry": 40}, {"ecutwfc_ry": 50}])
