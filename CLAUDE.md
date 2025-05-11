# Claude Project Assistant

This file contains information to help Claude work with this project effectively.

## Project Overview

Clinical Trial Search is a Python project aimed at improving the process of finding relevant clinical trials using LLMs to process and tag trial information.

## Development Setup

- Python project using uv for package management
- ruff for linting and formatting
- pyright for type checking
- pre-commit for git hooks

## Important Commands to Run

When making changes, run these commands to check code quality:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check code
pyright

# Run tests
pytest
```

## Project Structure

- `src/` - Source code
- `data/` - Data files
- `scripts/` - Utility scripts

## Git Workflow

Always run linting and type checking before committing changes. The pre-commit hooks should handle this automatically.