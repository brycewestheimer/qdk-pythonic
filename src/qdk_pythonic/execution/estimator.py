"""Resource estimator wrapping qsharp.estimate."""

from __future__ import annotations

import uuid
import warnings
from typing import TYPE_CHECKING, Any

from qdk_pythonic.exceptions import ExecutionError
from qdk_pythonic.execution._compat import import_qsharp

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


def _build_estimation_code(circuit: Circuit, op_name: str) -> str:
    """Generate Q# code for estimation, stripping measurements and raw Q#.

    The resource estimator requires Unit-returning operations, so all
    measurements and raw Q# fragments are filtered out before code
    generation.

    Args:
        circuit: The circuit to generate code for.
        op_name: The Q# operation name.

    Returns:
        A Q# operation definition string (Unit return type).
    """
    from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator
    from qdk_pythonic.core.instruction import RawQSharp

    raw_count = sum(
        1 for i in circuit.instructions if isinstance(i, RawQSharp)
    )
    if raw_count > 0:
        warnings.warn(
            f"Stripped {raw_count} raw Q# fragment(s) from estimation "
            "code. Raw fragments may contain measurements or return "
            "statements incompatible with the resource estimator.",
            stacklevel=3,
        )

    filtered_circuit = circuit.without_measurements_and_raw()
    generator = QSharpCodeGenerator()
    return generator.generate_operation(op_name, filtered_circuit)


def estimate_circuit(
    circuit: Circuit, params: dict[str, Any] | None = None
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
    qsharp = import_qsharp()

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


def estimate_and_parse(
    circuit: Circuit,
    params: dict[str, Any] | None = None,
    algorithm_name: str = "circuit",
    hamiltonian_info: dict[str, Any] | None = None,
) -> Any:
    """Estimate resources and return a structured result.

    Combines ``estimate_circuit()`` with
    ``parse_estimation_result()`` for convenience.

    Args:
        circuit: The circuit to estimate.
        params: Optional estimator parameters.
        algorithm_name: Label for the algorithm.
        hamiltonian_info: Optional chemistry metadata.

    Returns:
        A ChemistryResourceEstimate.
    """
    from qdk_pythonic.execution.chemistry_estimate import (
        parse_estimation_result,
    )

    raw = estimate_circuit(circuit, params=params)
    return parse_estimation_result(
        raw, algorithm_name=algorithm_name,
        hamiltonian_info=hamiltonian_info,
    )


def estimate_circuit_batch(
    circuit: Circuit | list[Circuit], params_list: list[dict[str, Any]]
) -> list[Any]:
    """Estimate resources for multiple parameter configurations.

    Generates and compiles the Q# operation once per circuit, then runs
    the estimator for each parameter set.

    When *circuit* is a list, each circuit is compiled separately and
    every parameter configuration is applied to each, yielding
    ``len(circuits) * len(params_list)`` results.

    Args:
        circuit: A single circuit or a list of circuits to estimate.
        params_list: A list of estimator parameter dicts.

    Returns:
        A list of resource estimation results.

    Raises:
        ExecutionError: If Q# compilation or any estimation fails.
        ImportError: If qsharp is not installed.
    """
    qsharp = import_qsharp()

    circuits = circuit if isinstance(circuit, list) else [circuit]

    results: list[Any] = []
    for circ in circuits:
        op_name = f"_qdk_est_{uuid.uuid4().hex[:8]}"
        qsharp_code = _build_estimation_code(circ, op_name)

        try:
            qsharp.eval(qsharp_code)
        except Exception as e:
            raise ExecutionError(
                f"Q# compilation failed for estimation '{op_name}': {e}\n"
                f"Generated Q#:\n{qsharp_code}"
            ) from e

        for params in params_list:
            try:
                result = qsharp.estimate(f"{op_name}()", params=params)
                results.append(result)
            except Exception as e:
                raise ExecutionError(
                    f"Resource estimation failed for '{op_name}': {e}"
                ) from e

    return results
