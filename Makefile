.PHONY: install lint format typecheck test test-integration test-all docs clean check

install:
	pip install -e ".[dev]"

lint:
	ruff check src/

format:
	ruff format src/ tests/

typecheck:
	mypy src/qdk_pythonic/ --strict

test:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-all:
	pytest tests/ -v

docs:
	cd docs && make html

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov
	rm -rf docs/_build
	find . -type d -name __pycache__ -exec rm -rf {} +

check: lint typecheck test
