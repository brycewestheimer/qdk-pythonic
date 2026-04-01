"""Unit tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from qdk_pythonic.exceptions import (
    CircuitError,
    CodegenError,
    ExecutionError,
    ParserError,
    QdkPythonicError,
    UnsupportedConstructError,
)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Tests for exception class relationships."""

    def test_base_class(self) -> None:
        assert issubclass(QdkPythonicError, Exception)

    @pytest.mark.parametrize(
        "exc_class",
        [
            CircuitError,
            CodegenError,
            ExecutionError,
            ParserError,
            UnsupportedConstructError,
        ],
    )
    def test_subclass_of_base(self, exc_class: type[Exception]) -> None:
        assert issubclass(exc_class, QdkPythonicError)

    @pytest.mark.parametrize(
        "exc_class",
        [
            CircuitError,
            CodegenError,
            ExecutionError,
            ParserError,
            UnsupportedConstructError,
        ],
    )
    def test_catchable_as_base(self, exc_class: type[Exception]) -> None:
        with pytest.raises(QdkPythonicError):
            raise exc_class("test message")

    @pytest.mark.parametrize(
        "exc_class",
        [
            QdkPythonicError,
            CircuitError,
            CodegenError,
            ExecutionError,
            ParserError,
            UnsupportedConstructError,
        ],
    )
    def test_str_works(self, exc_class: type[Exception]) -> None:
        err = exc_class("something went wrong")
        assert str(err) == "something went wrong"

    @pytest.mark.parametrize(
        "exc_class",
        [
            QdkPythonicError,
            CircuitError,
            CodegenError,
            ExecutionError,
            ParserError,
            UnsupportedConstructError,
        ],
    )
    def test_importable_from_module(self, exc_class: type[Exception]) -> None:
        import qdk_pythonic.exceptions as mod

        assert hasattr(mod, exc_class.__name__)
        assert getattr(mod, exc_class.__name__) is exc_class

    def test_empty_message(self) -> None:
        err = QdkPythonicError()
        assert str(err) == ""

    def test_exception_with_cause(self) -> None:
        cause = ValueError("root cause")
        err = ExecutionError("wrapper")
        err.__cause__ = cause
        assert err.__cause__ is cause
