"""Tests for FCIDUMP file support."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from qdk_pythonic.domains.chemistry.fcidump import (
    FCIDUMPData,
    read_fcidump,
    write_fcidump,
)
from qdk_pythonic.exceptions import ParserError

np = pytest.importorskip("numpy")


# Minimal H2 FCIDUMP content (2 spatial orbitals)
_H2_FCIDUMP = """\
 &FCI NORB=2,NELEC=2,MS2=0,
  ORBSYM=1,1,
  ISYM=1,
 &END
  6.7463390000e-01     1     1     1     1
  6.6368140000e-01     2     2     2     2
  6.6368140000e-01     1     1     2     2
  1.8127860000e-01     2     1     2     1
 -1.2525280000e+00     1     1     0     0
 -4.7590780000e-01     2     2     0     0
  7.1376600000e-01     0     0     0     0
"""


@pytest.mark.unit
def test_parse_h2() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write(_H2_FCIDUMP)
        path = f.name

    data = read_fcidump(path)
    Path(path).unlink()

    assert data.n_orbitals == 2
    assert data.n_electrons == 2
    assert data.ms2 == 0
    assert data.h1e.shape == (2, 2)
    assert data.h2e.shape == (2, 2, 2, 2)
    assert abs(data.nuclear_repulsion - 0.71376600) < 1e-6


@pytest.mark.unit
def test_h1e_hermitian() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write(_H2_FCIDUMP)
        path = f.name

    data = read_fcidump(path)
    Path(path).unlink()

    # h1e should be symmetric
    assert abs(data.h1e[0, 1] - data.h1e[1, 0]) < 1e-15


@pytest.mark.unit
def test_round_trip() -> None:
    """Write then read should recover the same data."""
    n = 2
    h1e = np.array([[1.0, 0.5], [0.5, 0.8]])
    h2e = np.zeros((n, n, n, n))
    h2e[0, 0, 0, 0] = 0.6
    h2e[1, 1, 1, 1] = 0.5

    original = FCIDUMPData(
        n_orbitals=n,
        n_electrons=2,
        ms2=0,
        h1e=h1e,
        h2e=h2e,
        nuclear_repulsion=0.7,
    )

    with tempfile.NamedTemporaryFile(
        suffix=".fcidump", delete=False,
    ) as f:
        path = f.name

    write_fcidump(path, original)
    recovered = read_fcidump(path)
    Path(path).unlink()

    assert recovered.n_orbitals == original.n_orbitals
    assert recovered.n_electrons == original.n_electrons
    assert recovered.ms2 == original.ms2
    assert abs(recovered.nuclear_repulsion - original.nuclear_repulsion) < 1e-10
    # h1e diagonal should match
    assert abs(recovered.h1e[0, 0] - 1.0) < 1e-10
    assert abs(recovered.h1e[1, 1] - 0.8) < 1e-10


@pytest.mark.unit
def test_to_fermion_operator() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write(_H2_FCIDUMP)
        path = f.name

    data = read_fcidump(path)
    Path(path).unlink()

    op = data.to_fermion_operator()
    assert len(op) > 0


@pytest.mark.unit
def test_to_hamiltonian() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write(_H2_FCIDUMP)
        path = f.name

    data = read_fcidump(path)
    Path(path).unlink()

    h = data.to_hamiltonian(mapping="jordan_wigner")
    assert len(h) > 0
    assert h.qubit_count() > 0


@pytest.mark.unit
def test_to_hamiltonian_bk() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write(_H2_FCIDUMP)
        path = f.name

    data = read_fcidump(path)
    Path(path).unlink()

    h = data.to_hamiltonian(mapping="bravyi_kitaev")
    assert len(h) > 0


@pytest.mark.unit
def test_invalid_no_header() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fcidump", delete=False,
    ) as f:
        f.write("not a valid fcidump\n")
        path = f.name

    with pytest.raises(ParserError, match="No &FCI"):
        read_fcidump(path)
    Path(path).unlink()


@pytest.mark.unit
def test_frozen() -> None:
    data = FCIDUMPData(
        n_orbitals=2, n_electrons=2, ms2=0,
        h1e=np.zeros((2, 2)), h2e=np.zeros((2, 2, 2, 2)),
        nuclear_repulsion=0.0,
    )
    with pytest.raises(AttributeError):
        data.n_orbitals = 3  # type: ignore[misc]
