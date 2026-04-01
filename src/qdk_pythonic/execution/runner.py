"""Simulation runner wrapping qsharp.eval and qsharp.run."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from qdk_pythonic.exceptions import ExecutionError
from qdk_pythonic.execution._compat import import_qsharp
from qdk_pythonic.execution.config import RunConfig

if TYPE_CHECKING:
    from qdk_pythonic.core.circuit import Circuit


def run_circuit(circuit: Circuit, config: RunConfig | None = None) -> list[Any]:
    """Execute a circuit on the qsharp simulator.

    Generates a named Q# operation from the circuit, compiles it via
    ``qsharp.eval``, then runs it with ``qsharp.run``.

    Args:
        circuit: The circuit to execute.
        config: Optional run configuration. Defaults to ``RunConfig()``.

    Returns:
        A list of measurement results, one per shot.

    Raises:
        ExecutionError: If Q# compilation or simulation fails.
        ImportError: If qsharp is not installed.
    """
    if config is None:
        config = RunConfig()

    qsharp = import_qsharp()

    from qdk_pythonic.codegen.qsharp import QSharpCodeGenerator

    op_name = f"_qdk_op_{uuid.uuid4().hex[:8]}"
    generator = QSharpCodeGenerator()
    qsharp_code = generator.generate_operation(op_name, circuit)

    try:
        qsharp.eval(qsharp_code)
    except Exception as e:
        raise ExecutionError(
            f"Q# compilation failed for '{op_name}': {e}\n"
            f"Generated Q#:\n{qsharp_code}"
        ) from e

    try:
        results = qsharp.run(f"{op_name}()", shots=config.shots)
    except Exception as e:
        raise ExecutionError(f"Simulation failed for '{op_name}': {e}") from e

    return list(results) if not isinstance(results, list) else results
