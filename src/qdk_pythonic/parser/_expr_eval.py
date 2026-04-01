"""Safe arithmetic expression evaluator for parser use."""

from __future__ import annotations

import ast
import operator

from qdk_pythonic.exceptions import ParserError

_BINARY_OPS: dict[type[ast.operator], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPS: dict[type[ast.unaryop], object] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.expr) -> float:
    """Recursively evaluate an AST node containing only arithmetic."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        op_fn = _BINARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return float(op_fn(left, right))  # type: ignore[operator]
    if isinstance(node, ast.UnaryOp):
        op_fn = _UNARY_OPS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return float(op_fn(_safe_eval_node(node.operand)))  # type: ignore[operator]
    raise ValueError(f"Unsupported expression node: {ast.dump(node)}")


def eval_math_expr(
    expr: str,
    constants: dict[str, float] | None = None,
) -> float:
    """Evaluate a simple arithmetic expression with named constants.

    Supports ``+``, ``-``, ``*``, ``/``, unary ``-``/``+``, numeric
    literals, and caller-supplied named constants.

    Args:
        expr: The expression string.
        constants: Mapping of names to float values (e.g. ``{"pi": 3.14...}``).

    Returns:
        The evaluated float result.

    Raises:
        ParserError: If the expression cannot be evaluated.
    """
    cleaned = expr.strip()

    # Substitute named constants (longest first to avoid partial matches)
    if constants:
        for name in sorted(constants, key=len, reverse=True):
            cleaned = cleaned.replace(name, repr(constants[name]))

    # Fast path: plain numeric literal
    try:
        return float(cleaned)
    except ValueError:
        pass

    # Safe AST evaluation
    try:
        tree = ast.parse(cleaned, mode="eval")
        return _safe_eval_node(tree.body)
    except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as e:
        raise ParserError(f"Cannot evaluate expression: {expr!r}") from e
