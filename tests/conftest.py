"""Shared test configuration and fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast tests, no qsharp needed")
    config.addinivalue_line("markers", "integration: requires qsharp package")
