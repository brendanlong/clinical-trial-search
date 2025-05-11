# Claude Project Assistant

This file contains information to help Claude work with this project effectively.

## Project Overview

Clinical Trial Search is a Python project aimed at improving the process of finding relevant clinical trials using LLMs to process and tag trial information.

## Development Setup

- Python project using uv for package management
  - Always use `uv add <package>` to install dependencies
  - After adding dependencies to pyproject.toml, run `uv sync` to update lock file
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

- `src/clinical_trial_search/` - Main package source code
  - `downloaders/` - Trial data downloading components
  - `processors/` - LLM processing and tagging components
- `data/` - Data files
  - `raw/` - Raw downloaded trial data
- `scripts/` - Command-line utilities
  - `download_trials.py` - Script to download trial data
  - `process_trials.py` - Script to process trials with LLMs
- `tests/` - Test files (to be implemented)

## Key Files

- `src/clinical_trial_search/downloaders/aact.py` - AACT data downloader (downloads from AACT's static database copies)
- `src/clinical_trial_search/processors/llm_tagger.py` - LLM processor for trial tagging

## Prompt Engineering

The LLM tagger uses a carefully designed prompt that instructs the model to:
- Analyze clinical trial information
- Generate standardized tags for conditions
- Simplify eligibility criteria into plain language
- Categorize trials by mechanism and targets
- Score relevance for different disease stages

The prompt can be found in `generate_trial_tags()` method in `llm_tagger.py`.

## Git Workflow

Always run linting and type checking before committing changes. The pre-commit hooks should handle this automatically.

## Customizing LLM Configuration

The LLM processor accepts the following configurations:
- `api_key`: API key for the LLM service
- `api_url`: URL for the LLM API (defaults to Anthropic's Claude API)
- `model`: Model to use (defaults to claude-3-sonnet-20240229)