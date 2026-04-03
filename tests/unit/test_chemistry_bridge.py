"""Tests for qsharp.chemistry bridge (mocked, no qsharp needed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from qdk_pythonic.execution.chemistry_bridge import (
    ChemistryEstimationConfig,
)


@pytest.mark.unit
def test_config_defaults() -> None:
    cfg = ChemistryEstimationConfig()
    assert cfg.error_budget == 0.01
    assert cfg.qubit_params == "qubit_gate_ns_e3"
    assert cfg.qec_scheme == "surface_code"


@pytest.mark.unit
def test_config_to_estimator_params() -> None:
    cfg = ChemistryEstimationConfig(
        error_budget=0.001,
        qubit_params="qubit_gate_us_e4",
        qec_scheme="floquet_code",
    )
    params = cfg.to_estimator_params()
    assert params["errorBudget"] == 0.001
    assert params["qubitParams"]["name"] == "qubit_gate_us_e4"
    assert params["qecScheme"]["name"] == "floquet_code"


@pytest.mark.unit
def test_config_frozen() -> None:
    cfg = ChemistryEstimationConfig()
    with pytest.raises(AttributeError):
        cfg.error_budget = 0.1  # type: ignore[misc]


@pytest.mark.unit
def test_import_error_no_qsharp() -> None:
    """Verify clear error when qsharp is missing."""
    from qdk_pythonic.execution.chemistry_bridge import (
        _import_qsharp_chemistry,
    )

    with patch.dict("sys.modules", {"qsharp": None}):
        with pytest.raises(ImportError, match="qsharp is required"):
            _import_qsharp_chemistry()


@pytest.mark.unit
def test_estimate_chemistry_calls_bridge() -> None:
    """Mock the bridge call and verify data flow."""
    np = pytest.importorskip("numpy")
    from qdk_pythonic.domains.chemistry.fcidump import FCIDUMPData
    from qdk_pythonic.execution.chemistry_bridge import estimate_chemistry

    data = FCIDUMPData(
        n_orbitals=2, n_electrons=2, ms2=0,
        h1e=np.zeros((2, 2)), h2e=np.zeros((2, 2, 2, 2)),
        nuclear_repulsion=0.7,
    )

    mock_result = {
        "logicalCounts": {"numQubits": 50, "tCount": 1000},
        "physicalCounts": {"physicalQubits": 10000, "runtime": 1000000},
        "physicalCountsFormatted": {"runtime": "1 sec"},
        "logicalQubit": {"codeDistance": 11},
        "jobParams": {
            "qubitParams": {"name": "qubit_gate_ns_e3"},
            "qecScheme": {"name": "surface_code"},
            "errorBudget": 0.01,
        },
    }

    mock_chem = MagicMock()
    mock_chem.estimate_from_fcidump.return_value = mock_result

    with patch(
        "qdk_pythonic.execution.chemistry_bridge._import_qsharp_chemistry",
        return_value=(MagicMock(), mock_chem),
    ):
        result = estimate_chemistry(data)

    assert result.algorithm_name == "df_qubitization"
    assert result.logical.logical_qubits == 50
    assert result.physical.physical_qubits == 10000
    assert result.hamiltonian_info["n_orbitals"] == 2
