"""Symbolic parameter for variational circuits."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parameter:
    """A named symbolic parameter for rotation angles.

    Use ``Parameter`` instances as rotation angles in circuit gate
    methods to build parameterized circuit templates. Call
    ``Circuit.bind_parameters()`` to substitute concrete values
    before code generation or execution.

    Example::

        from qdk_pythonic import Circuit
        from qdk_pythonic.core.parameter import Parameter

        theta = Parameter("theta")
        circ = Circuit()
        q = circ.allocate(1)
        circ.ry(theta, q[0])

        bound = circ.bind_parameters({"theta": 0.5})
        print(bound.to_qsharp())

    Attributes:
        name: The parameter name.
    """

    name: str
