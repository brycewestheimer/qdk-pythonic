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
   make check   # runs lint + typecheck + unit tests
   ```
4. Open a pull request.

## Code style

- **Linting:** `ruff check src/` (line length 99)
- **Formatting:** `ruff format src/ tests/`
- **Type checking:** `mypy src/qdk_pythonic/ --strict`
- **Docstrings:** Google style
- **Commits:** Conventional commit format (`type(scope): description`)

## Tests

Unit tests require no external dependencies:

```bash
pytest tests/unit/ -v
```

Integration tests require the `qsharp` package:

```bash
pip install -e ".[qsharp]"
pytest tests/integration/ -v
```

## Reporting issues

Use GitHub Issues with the provided templates for bug reports and feature requests.
