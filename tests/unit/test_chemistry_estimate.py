"""Tests for structured chemistry resource estimation results."""

from __future__ import annotations

import pytest

from qdk_pythonic.execution.chemistry_estimate import (
    ChemistryResourceEstimate,
    LogicalResources,
    PhysicalResources,
    compare_estimates,
    parse_estimation_result,
)


def _mock_raw_result() -> dict:
    """A mock qsharp.estimate() result dict."""
    return {
        "logicalCounts": {
            "numQubits": 100,
            "tCount": 50000,
            "rotationCount": 2000,
            "rotationDepth": 500,
            "cczCount": 300,
            "measurementCount": 100,
        },
        "physicalCounts": {
            "physicalQubits": 200000,
            "runtime": 3600000000,  # microseconds -> 3600 seconds
            "breakdown": {
                "numTfactories": 15,
                "physicalQubitsForTfactories": 50000,
            },
        },
        "physicalCountsFormatted": {
            "runtime": "1 hour",
        },
        "logicalQubit": {
            "codeDistance": 17,
        },
        "jobParams": {
            "qubitParams": {"name": "qubit_gate_ns_e3"},
            "qecScheme": {"name": "surface_code"},
            "errorBudget": 0.01,
        },
    }


@pytest.mark.unit
def test_parse_extracts_logical() -> None:
    result = parse_estimation_result(_mock_raw_result())
    assert result.logical.logical_qubits == 100
    assert result.logical.t_count == 50000
    assert result.logical.rotation_count == 2000
    assert result.logical.rotation_depth == 500
    assert result.logical.ccz_count == 300
    assert result.logical.measurement_count == 100


@pytest.mark.unit
def test_parse_extracts_physical() -> None:
    result = parse_estimation_result(_mock_raw_result())
    assert result.physical.physical_qubits == 200000
    assert abs(result.physical.runtime_seconds - 3600.0) < 0.01
    assert result.physical.runtime_human == "1 hour"
    assert result.physical.code_distance == 17
    assert result.physical.t_factory_count == 15
    assert result.physical.t_factory_fraction > 0.0


@pytest.mark.unit
def test_parse_extracts_params() -> None:
    result = parse_estimation_result(
        _mock_raw_result(), algorithm_name="trotter_qpe",
    )
    assert result.algorithm_name == "trotter_qpe"
    assert result.qubit_model == "qubit_gate_ns_e3"
    assert result.qec_scheme == "surface_code"
    assert result.error_budget == 0.01


@pytest.mark.unit
def test_parse_with_hamiltonian_info() -> None:
    info = {"n_orbitals": 4, "n_electrons": 2, "one_norm": 5.0}
    result = parse_estimation_result(
        _mock_raw_result(), hamiltonian_info=info,
    )
    assert result.hamiltonian_info["n_orbitals"] == 4


@pytest.mark.unit
def test_parse_missing_keys_uses_defaults() -> None:
    """Empty dict should not raise, just use zeros."""
    result = parse_estimation_result({})
    assert result.logical.logical_qubits == 0
    assert result.physical.physical_qubits == 0
    assert result.physical.runtime_seconds == 0.0
    assert result.qubit_model == "unknown"
    assert result.qec_scheme == "unknown"


@pytest.mark.unit
def test_raw_result_preserved() -> None:
    raw = _mock_raw_result()
    result = parse_estimation_result(raw)
    assert result.raw_result is raw


@pytest.mark.unit
def test_print_report(capsys: pytest.CaptureFixture[str]) -> None:
    result = parse_estimation_result(
        _mock_raw_result(), algorithm_name="test",
    )
    result.print_report()
    captured = capsys.readouterr()
    assert "Chemistry Resource Estimate" in captured.out
    assert "Logical qubits" in captured.out
    assert "Physical qubits" in captured.out


@pytest.mark.unit
def test_print_report_with_ham_info(
    capsys: pytest.CaptureFixture[str],
) -> None:
    info = {"n_orbitals": 4}
    result = parse_estimation_result(
        _mock_raw_result(), hamiltonian_info=info,
    )
    result.print_report()
    captured = capsys.readouterr()
    assert "Hamiltonian info" in captured.out
    assert "n_orbitals" in captured.out


@pytest.mark.unit
def test_to_dict_flat() -> None:
    info = {"n_orbitals": 4}
    result = parse_estimation_result(
        _mock_raw_result(),
        algorithm_name="test",
        hamiltonian_info=info,
    )
    d = result.to_dict()
    assert d["algorithm_name"] == "test"
    assert d["logical_qubits"] == 100
    assert d["physical_qubits"] == 200000
    assert d["ham_n_orbitals"] == 4


@pytest.mark.unit
def test_compare_estimates() -> None:
    r1 = parse_estimation_result(
        _mock_raw_result(), algorithm_name="a",
    )
    r2 = parse_estimation_result(
        _mock_raw_result(), algorithm_name="b",
    )
    table = compare_estimates([r1, r2])
    assert len(table) == 2
    assert table[0]["algorithm_name"] == "a"
    assert table[1]["algorithm_name"] == "b"


@pytest.mark.unit
def test_logical_resources_frozen() -> None:
    lr = LogicalResources(
        logical_qubits=10, t_count=100,
        rotation_count=50, rotation_depth=20,
        ccz_count=5, measurement_count=10,
    )
    with pytest.raises(AttributeError):
        lr.t_count = 200  # type: ignore[misc]


@pytest.mark.unit
def test_physical_resources_frozen() -> None:
    pr = PhysicalResources(
        physical_qubits=1000, runtime_seconds=60.0,
        runtime_human="1 min", code_distance=11,
        t_factory_count=5, t_factory_fraction=0.2,
    )
    with pytest.raises(AttributeError):
        pr.physical_qubits = 2000  # type: ignore[misc]


@pytest.mark.unit
def test_chemistry_resource_estimate_frozen() -> None:
    result = parse_estimation_result(_mock_raw_result())
    with pytest.raises(AttributeError):
        result.algorithm_name = "x"  # type: ignore[misc]
