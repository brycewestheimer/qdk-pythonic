"""Tests for the algorithm registry system."""

from __future__ import annotations

import pytest

from qdk_pythonic.registry import (
    Algorithm,
    Settings,
    _factories,
    available,
    create,
    register,
)


class _DummySettings(Settings):
    def __init__(self) -> None:
        super().__init__()
        self._set_default("param", 42, int, "A test parameter")


class _DummyAlgorithm(Algorithm):
    def __init__(self) -> None:
        super().__init__()
        self._settings = _DummySettings()

    def type_name(self) -> str:
        return "test_type"

    def name(self) -> str:
        return "dummy"

    def _run_impl(self, x: int) -> int:
        return x * self._settings.get("param")


@pytest.fixture(autouse=True)
def _clean_registry():  # type: ignore[no-untyped-def]
    """Clear registry between tests."""
    original = list(_factories)
    yield
    _factories.clear()
    _factories.extend(original)


@pytest.mark.unit
def test_register_and_create() -> None:
    register(lambda: _DummyAlgorithm())
    algo = create("test_type", "dummy")
    assert algo.run(2) == 84


@pytest.mark.unit
def test_create_with_settings() -> None:
    register(lambda: _DummyAlgorithm())
    algo = create("test_type", "dummy", param=10)
    assert algo.run(3) == 30


@pytest.mark.unit
def test_create_default_name() -> None:
    register(lambda: _DummyAlgorithm())
    algo = create("test_type")  # no name -> default
    assert algo.name() == "dummy"


@pytest.mark.unit
def test_create_unknown_type() -> None:
    with pytest.raises(KeyError, match="not found"):
        create("nonexistent_type")


@pytest.mark.unit
def test_create_unknown_name() -> None:
    register(lambda: _DummyAlgorithm())
    with pytest.raises(KeyError, match="not found"):
        create("test_type", "nonexistent")


@pytest.mark.unit
def test_available() -> None:
    register(lambda: _DummyAlgorithm())
    avail = available()
    assert "test_type" in avail
    assert "dummy" in avail["test_type"]


@pytest.mark.unit
def test_settings_lock_after_run() -> None:
    register(lambda: _DummyAlgorithm())
    algo = create("test_type", "dummy")
    algo.run(1)  # locks settings
    with pytest.raises(RuntimeError, match="locked"):
        algo.settings().set("param", 99)


@pytest.mark.unit
def test_settings_unknown_key() -> None:
    s = _DummySettings()
    with pytest.raises(KeyError, match="Unknown setting"):
        s.set("nonexistent", 42)


@pytest.mark.unit
def test_multiple_implementations_same_type() -> None:
    """Two algorithms of the same type coexist in one factory."""

    class _AltAlgorithm(_DummyAlgorithm):
        def name(self) -> str:
            return "alt"

        def _run_impl(self, x: int) -> int:
            return x + self._settings.get("param")

    register(lambda: _DummyAlgorithm())
    register(lambda: _AltAlgorithm())

    assert create("test_type", "dummy").run(2) == 84
    assert create("test_type", "alt").run(2) == 44


@pytest.mark.unit
def test_aliases() -> None:
    class _AliasedAlgorithm(_DummyAlgorithm):
        def aliases(self) -> list[str]:
            return ["dummy", "dummy_v2", "test"]

    register(lambda: _AliasedAlgorithm())
    # All aliases should resolve to the same algorithm
    assert create("test_type", "dummy").run(1) == 42
    assert create("test_type", "dummy_v2").run(1) == 42
    assert create("test_type", "test").run(1) == 42
