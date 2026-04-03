"""Tests for double-factorized Hamiltonian representation."""

from __future__ import annotations

import pytest

from qdk_pythonic.exceptions import CircuitError

np = pytest.importorskip("numpy")

from qdk_pythonic.domains.common.double_factorization import (
    DoubleFactorizedHamiltonian,
    double_factorize,
    from_fcidump,
)


def _h2_integrals() -> tuple[object, object, float]:
    """Minimal H2 integrals (2 spatial orbitals)."""
    h1e = np.array([[-1.25, 0.0], [0.0, -0.48]])
    h2e = np.zeros((2, 2, 2, 2))
    h2e[0, 0, 0, 0] = 0.67
    h2e[1, 1, 1, 1] = 0.70
    h2e[0, 0, 1, 1] = 0.66
    h2e[1, 1, 0, 0] = 0.66
    h2e[0, 1, 1, 0] = 0.18
    h2e[1, 0, 0, 1] = 0.18
    nuclear_repulsion = 0.71
    return h1e, h2e, nuclear_repulsion


@pytest.mark.unit
def test_factorize_h2_basic() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    assert df.n_orbitals == 2
    assert df.n_electrons == 2
    assert df.n_leaves > 0
    assert df.one_norm() > 0.0


@pytest.mark.unit
def test_factorize_shapes() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    assert df.one_body_integrals.shape == (2, 2)
    assert df.leaf_matrices.shape[0] == df.n_leaves
    assert df.leaf_matrices.shape[1:] == (2, 2)
    assert len(df.leaf_signs) == df.n_leaves


@pytest.mark.unit
def test_higher_threshold_fewer_leaves() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df_low = double_factorize(h1e, h2e, nuc, n_electrons=2, threshold=1e-10)
    df_high = double_factorize(h1e, h2e, nuc, n_electrons=2, threshold=0.5)
    assert df_high.n_leaves <= df_low.n_leaves


@pytest.mark.unit
def test_round_trip_reconstruction() -> None:
    """Reconstructed h2e should match the original."""
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2, threshold=1e-12)
    fcidump = df.to_fcidump_data()

    assert fcidump.h1e.shape == (2, 2)
    assert fcidump.h2e.shape == (2, 2, 2, 2)

    h2e_recon = fcidump.h2e
    diff = np.max(np.abs(np.asarray(h2e) - h2e_recon))
    assert diff < 1e-10


@pytest.mark.unit
def test_summary_keys() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    s = df.summary()
    expected_keys = {
        "n_orbitals", "n_electrons", "n_leaves",
        "one_norm", "nuclear_repulsion",
        "one_body_correction", "cholesky_threshold",
    }
    assert set(s.keys()) == expected_keys


@pytest.mark.unit
def test_print_summary(capsys: pytest.CaptureFixture[str]) -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    df.print_summary()
    captured = capsys.readouterr()
    assert "DoubleFactorizedHamiltonian" in captured.out
    assert "Leaves" in captured.out
    assert "1-norm" in captured.out


@pytest.mark.unit
def test_to_pauli_hamiltonian() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2, threshold=1e-10)
    pauli_h = df.to_pauli_hamiltonian()
    assert len(pauli_h) > 0
    assert pauli_h.qubit_count() > 0


@pytest.mark.unit
def test_from_fcidump() -> None:
    from qdk_pythonic.domains.chemistry.fcidump import FCIDUMPData

    h1e_arr = np.array([[-1.0, 0.0], [0.0, -0.5]])
    h2e_arr = np.zeros((2, 2, 2, 2))
    h2e_arr[0, 0, 0, 0] = 0.5
    data = FCIDUMPData(
        n_orbitals=2, n_electrons=2, ms2=0,
        h1e=h1e_arr, h2e=h2e_arr, nuclear_repulsion=0.7,
    )
    df = from_fcidump(data)
    assert df.n_orbitals == 2
    assert df.n_electrons == 2


@pytest.mark.unit
def test_trivial_zero_h2e() -> None:
    """Zero two-body integrals should produce zero leaves."""
    h1e = np.array([[-1.0, 0.0], [0.0, -0.5]])
    h2e = np.zeros((2, 2, 2, 2))
    df = double_factorize(h1e, h2e, 0.0, n_electrons=2)
    assert df.n_leaves == 0


@pytest.mark.unit
def test_leaf_signs_are_valid() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    for s in df.leaf_signs:
        assert s in (1, -1)


@pytest.mark.unit
def test_frozen() -> None:
    h1e, h2e, nuc = _h2_integrals()
    df = double_factorize(h1e, h2e, nuc, n_electrons=2)
    with pytest.raises(AttributeError):
        df.n_orbitals = 5  # type: ignore[misc]


@pytest.mark.unit
def test_invalid_h1e_shape() -> None:
    h2e = np.zeros((2, 2, 2, 2))
    with pytest.raises(CircuitError, match="h1e must be"):
        double_factorize(np.zeros((3, 2)), h2e, 0.0, n_electrons=2)


@pytest.mark.unit
def test_invalid_h2e_shape() -> None:
    h1e = np.zeros((2, 2))
    with pytest.raises(CircuitError, match="h2e must be"):
        double_factorize(h1e, np.zeros((2, 2, 2)), 0.0, n_electrons=2)
