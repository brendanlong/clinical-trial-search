# Contributing to Clinical Trial Search

## Development Environment

This project is developed in Python. We use the following tools:

### uv

We use [uv](https://github.com/astral-sh/uv) for package management and virtual environment management. This provides faster installations and better dependency resolution than traditional pip.

To install uv:
```bash
pip install uv
```

### ruff

[Ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter and formatter written in Rust. We use it to enforce consistent code style and catch common issues.

### pyright

[Pyright](https://github.com/microsoft/pyright) is a fast type checker for Python that helps catch type-related errors before runtime.

### pre-commit

We use [pre-commit](https://pre-commit.com/) to run checks automatically before each commit, ensuring code quality and consistency.

## Setup

1. Clone the repository
2. Run `uv venv` to create a virtual environment
3. Activate the virtual environment:
   - On Unix/MacOS: `source .venv/bin/activate`
   - On Windows: `.venv\Scripts\activate`
4. Run `uv pip install -e '.[dev]'` to install dependencies including development tools
5. Run `pre-commit install` to install the pre-commit hooks

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) guidelines
- Use type hints for all function parameters and return values
- Write clear docstrings for all modules, classes, and functions

## Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Run tests and ensure all checks pass
5. Submit a pull request

Pull requests should include appropriate tests and documentation updates.