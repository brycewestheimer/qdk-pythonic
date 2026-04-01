"""Resource estimator wrapping qsharp.estimate."""

from __future__ import annotations

import uuid
from typing import Any

from qdk_pythonic.exceptions import ExecutionError


def _import_qsharp() -> Any:
    """Lazily import qsharp, raising a clear error if not installed.

    Returns:
        The qsharp module.

    Raises:
        ImportError: If qsharp is not installed.
    """
    try:
        import qsharp  # type: ignore[import-not-found]

        return qsharp
    except ImportError:
        raise ImportError(
            "qsharp is required for resource estimation. "
            "Install it with: pip install 'qdk-pythonic[qsharp]'"
        ) from None


def _build_estimation_code(circuit: Any, op_name: str) -> str:
    """Generate Q# code for estimation, stripping measurements.

    The resource estimator requires Unit-returning operations, so all
    measurements are filtered out before code generation.

    Args:
        circuit: The circuit to generate code for.
        op_name: The Q# operation name.

    Returns:
        A Q# operation definition string (Unit return type).
    """
    from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
    from qdk_pythonic.core.instruction import Measurement

    # Filter out measurements for estimation (must return Unit)
    filtered = [
        inst for inst in circuit._instructions
        if not isinstance(inst, Measurement)
    ]

    original = circuit._instructions
    circuit._instructions = filtered
    try:
        generator = QSharpCodeGenerator()
        return generator.generate_operation(op_name, circuit)
    finally:
        circuit._instructions = original


def estimate_circuit(
    circuit: Any, params: dict[str, Any] | None = None
) -> Any:
    """Estimate resources for a circuit.

    Generates a Q# operation without measurements (Unit return type),
    compiles it, then runs the resource estimator.

    Args:
        circuit: The circuit to estimate.
        params: Optional estimator parameters (e.g. qubit model, QEC scheme).

    Returns:
        The resource estimation result from qsharp.estimate.

    Raises:
        ExecutionError: If Q# compilation or estimation fails.
        ImportError: If qsharp is not installed.
    """
    qsharp = _import_qsharp()

    op_name = f"_qdk_est_{uuid.uuid4().hex[:8]}"
    qsharp_code = _build_estimation_code(circuit, op_name)

    try:
        qsharp.eval(qsharp_code)
    except Exception as e:
        raise ExecutionError(
            f"Q# compilation failed for estimation '{op_name}': {e}\n"
            f"Generated Q#:\n{qsharp_code}"
        ) from e

    est_kwargs: dict[str, Any] = {}
    if params is not None:
        est_kwargs["params"] = params

    try:
        result = qsharp.estimate(f"{op_name}()", **est_kwargs)
    except Exception as e:
        raise ExecutionError(
            f"Resource estimation failed for '{op_name}': {e}"
        ) from e

    return result


def estimate_circuit_batch(
    circuit: Any, params_list: list[dict[str, Any]]
) -> list[Any]:
    """Estimate resources for multiple parameter configurations.

    Generates and compiles the Q# operation once, then runs the estimator
    for each parameter set.

    Args:
        circuit: The circuit to estimate.
        params_list: A list of estimator parameter dicts.

    Returns:
        A list of resource estimation results, one per parameter set.

    Raises:
        ExecutionError: If Q# compilation or any estimation fails.
        ImportError: If qsharp is not installed.
    """
    qsharp = _import_qsharp()

    op_name = f"_qdk_est_{uuid.uuid4().hex[:8]}"
    qsharp_code = _build_estimation_code(circuit, op_name)

    try:
        qsharp.eval(qsharp_code)
    except Exception as e:
        raise ExecutionError(
            f"Q# compilation failed for estimation '{op_name}': {e}\n"
            f"Generated Q#:\n{qsharp_code}"
        ) from e

    results: list[Any] = []
    for params in params_list:
        try:
            result = qsharp.estimate(f"{op_name}()", params=params)
            results.append(result)
        except Exception as e:
            raise ExecutionError(
                f"Resource estimation failed for '{op_name}': {e}"
            ) from e

    return results
