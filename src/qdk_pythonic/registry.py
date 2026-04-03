"""Lightweight algorithm registry matching the QDK/Chemistry create() pattern.

Enables swappable implementations and plugin registration.

Example::

    from qdk_pythonic.registry import create

    builder = create("hamiltonian_builder", "quspin")
    hamiltonian = builder.run(static_list, n_sites=8)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

__all__ = [
    "Algorithm",
    "AlgorithmFactory",
    "Settings",
    "available",
    "create",
    "register",
    "register_factory",
]


class Settings:
    """Typed, validatable settings for an algorithm.

    Mirrors qdk_chemistry.data.Settings.
    """

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}
        self._types: dict[str, type] = {}
        self._descriptions: dict[str, str] = {}
        self._locked = False

    def _set_default(
        self,
        key: str,
        value: Any,
        value_type: type = object,
        description: str = "",
    ) -> None:
        self._defaults[key] = value
        self._values[key] = value
        self._types[key] = value_type
        self._descriptions[key] = description

    def get(self, key: str) -> Any:
        return self._values[key]

    def set(self, key: str, value: Any) -> None:
        if self._locked:
            raise RuntimeError("Settings are locked after run() is called")
        if key not in self._defaults:
            raise KeyError(f"Unknown setting: '{key}'")
        self._values[key] = value

    def update(self, kwargs: dict[str, Any]) -> None:
        for k, v in kwargs.items():
            self.set(k, v)

    def lock(self) -> None:
        self._locked = True

    def to_dict(self) -> dict[str, Any]:
        return dict(self._values)

    def describe(self) -> list[tuple[str, Any, str]]:
        """Return (key, default, description) for each setting."""
        return [
            (k, self._defaults[k], self._descriptions.get(k, ""))
            for k in self._defaults
        ]


class Algorithm(ABC):
    """Base class for registered algorithms.

    Mirrors qdk_chemistry.algorithms.base.Algorithm.
    """

    def __init__(self) -> None:
        self._settings = Settings()

    @abstractmethod
    def type_name(self) -> str:
        """Algorithm type, e.g. 'hamiltonian_builder', 'circuit_builder'."""

    @abstractmethod
    def name(self) -> str:
        """Implementation name, e.g. 'quspin', 'networkx_maxcut'."""

    def aliases(self) -> list[str]:
        return [self.name()]

    def settings(self) -> Settings:
        return self._settings

    @abstractmethod
    def _run_impl(self, *args: Any, **kwargs: Any) -> Any:
        """Implementation of the algorithm logic."""

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the algorithm. Locks settings, then delegates."""
        self._settings.lock()
        return self._run_impl(*args, **kwargs)


class AlgorithmFactory(ABC):
    """Factory for a specific algorithm type.

    Mirrors qdk_chemistry.algorithms.base.AlgorithmFactory.
    """

    def __init__(self) -> None:
        self._registry: dict[str, Callable[[], Algorithm]] = {}

    @abstractmethod
    def algorithm_type_name(self) -> str: ...

    @abstractmethod
    def default_algorithm_name(self) -> str: ...

    def create(self, name: str | None = None) -> Algorithm:
        if not name:
            name = self.default_algorithm_name()
        if name not in self._registry:
            raise KeyError(
                f"Algorithm '{name}' not found for type "
                f"'{self.algorithm_type_name()}'. "
                f"Available: {list(self._registry.keys())}"
            )
        return self._registry[name]()

    def register_instance(
        self, generator: Callable[[], Algorithm],
    ) -> None:
        instance = generator()
        for alias in instance.aliases():
            self._registry[alias] = generator

    def available(self) -> list[str]:
        return list(self._registry.keys())


# ── Global Registry ──

_factories: list[AlgorithmFactory] = []


def register_factory(factory: AlgorithmFactory) -> None:
    """Register a new algorithm factory."""
    _factories.append(factory)


def register(generator: Callable[[], Algorithm]) -> None:
    """Register an algorithm implementation.

    Inspects the instance's type_name() to find the matching factory.
    If no factory exists for that type, creates one automatically.
    """
    instance = generator()
    type_name = instance.type_name()

    for factory in _factories:
        if factory.algorithm_type_name() == type_name:
            factory.register_instance(generator)
            return

    # Auto-create a factory for this type
    factory = _AutoFactory(type_name, instance.name())
    factory.register_instance(generator)
    _factories.append(factory)


def create(
    algorithm_type: str,
    algorithm_name: str | None = None,
    **kwargs: Any,
) -> Algorithm:
    """Create an algorithm instance by type and name.

    Mirrors qdk_chemistry.algorithms.registry.create().

    Args:
        algorithm_type: The type of algorithm
            (e.g. "hamiltonian_builder").
        algorithm_name: The specific implementation. If None,
            uses the factory default.
        **kwargs: Settings to configure the algorithm.

    Returns:
        Algorithm instance, ready to .run().
    """
    for factory in _factories:
        if factory.algorithm_type_name() == algorithm_type:
            instance = factory.create(algorithm_name)
            if kwargs:
                instance.settings().update(kwargs)
            return instance

    available_types = [f.algorithm_type_name() for f in _factories]
    raise KeyError(
        f"Algorithm type '{algorithm_type}' not found. "
        f"Available types: {available_types}"
    )


def available(algorithm_type: str | None = None) -> dict[str, list[str]]:
    """List available algorithm types and implementations.

    Mirrors qdk_chemistry.algorithms.registry.available().
    """
    result: dict[str, list[str]] = {}
    for factory in _factories:
        if (
            algorithm_type is None
            or factory.algorithm_type_name() == algorithm_type
        ):
            result[factory.algorithm_type_name()] = factory.available()
    return result


class _AutoFactory(AlgorithmFactory):
    """Factory auto-created when registering with no existing factory."""

    def __init__(self, type_name: str, default_name: str) -> None:
        super().__init__()
        self._type_name = type_name
        self._default_name = default_name

    def algorithm_type_name(self) -> str:
        return self._type_name

    def default_algorithm_name(self) -> str:
        return self._default_name
