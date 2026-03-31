"""Custom exception hierarchy for qdk-pythonic."""


class QdkPythonicError(Exception):
    """Base exception for all qdk-pythonic errors."""


class CircuitError(QdkPythonicError):
    """Error in circuit construction or validation."""


class CodegenError(QdkPythonicError):
    """Error during code generation."""


class ExecutionError(QdkPythonicError):
    """Error during circuit execution or estimation."""


class ParserError(QdkPythonicError):
    """Error during parsing of Q# or OpenQASM source."""


class UnsupportedConstructError(QdkPythonicError):
    """A construct is not supported by the target backend."""
