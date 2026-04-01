# Contributing to qdk-pythonic

Thanks for your interest in contributing.

## Setup

```bash
git clone https://github.com/westh/qdk-pythonic.git
cd qdk-pythonic
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Development workflow

1. Create a branch from `main`.
2. Make your changes.
3. Run checks:
   ```bash
   ruff check src/
   mypy src/qdk_pythonic/ --strict
   pytest tests/unit/ -v
   ```
4. Open a pull request.

## Code style

- **Linting:** `ruff check src/` (line length 99)
- **Formatting:** `ruff format src/ tests/`
- **Type checking:** `mypy src/qdk_pythonic/ --strict`
- **Docstrings:** Google style with Args, Returns, Raises sections
- **Python:** 3.10+ (`X | Y` union syntax, not `Optional`)
- **Commits:** Conventional commit format (`type(scope): description`)

## Tests

Tests use pytest with two markers:

- `@pytest.mark.unit` -- no external dependencies
- `@pytest.mark.integration` -- requires `qsharp >= 1.25`

```bash
# Unit tests only
pytest -m unit -v

# Integration tests (requires qsharp)
pip install -e ".[qsharp]"
pytest -m integration -v
```

## Project structure

```
src/qdk_pythonic/
    core/          # Circuit, Qubit, Gate, Instruction data model
    codegen/       # Q# and OpenQASM code generators
    parser/        # Q# and OpenQASM parsers
    execution/     # Simulation runner and resource estimator
    analysis/      # Metrics, serialization, visualization
    exceptions.py  # Exception hierarchy
```

## Reporting issues

Use GitHub Issues with the provided templates for bug reports and feature requests.
