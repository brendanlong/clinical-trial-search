# Claude Project Assistant

This file contains information to help Claude work with this project effectively.

## Project Overview

Clinical Trial Search is a Python project aimed at improving the process of finding relevant clinical trials using LLMs to process and tag trial information.

## Development Setup

- Python project using uv for package management
  - Always use `uv add <package>` to install dependencies
  - After adding dependencies to pyproject.toml, run `uv sync` to update lock file
- Docker and Docker Compose for PostgreSQL database management
- ruff for linting and formatting
- pyright for type checking
- pre-commit for git hooks
- Don't add comments that are obvious
- Don't catch exceptions just to log them, prefer to let exceptions get thrown

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

For database operations:

```bash
# Start PostgreSQL database
docker-compose up -d

# Stop PostgreSQL database
docker-compose down

# Connect to PostgreSQL database
docker exec -it clinical-trial-postgres psql -U postgres -d aact

# Execute a specific SQL query
docker exec -i clinical-trial-postgres psql -U postgres -d aact -c 'SELECT * FROM ctgov.studies LIMIT 5'
```

### AACT Database Structure

The AACT database (Aggregate Analysis of ClinicalTrials.gov) contains comprehensive clinical trial data in a PostgreSQL schema called `ctgov`. Key tables include:

- `ctgov.studies` - Main table with core trial information
- `ctgov.conditions` - Medical conditions being studied
- `ctgov.eligibilities` - Eligibility criteria for participants
- `ctgov.interventions` - Treatment interventions being tested
- `ctgov.brief_summaries` and `ctgov.detailed_descriptions` - Trial descriptions

See `AACT_DB.md` for detailed database schema information and important columns for the clinical trial search functionality.

## Project Structure

Use `tree` on startup to understand the project structure.

## Key Files

- `src/clinical_trial_search/downloaders/aact.py` - AACT data downloader (downloads from AACT's static database copies)
- `src/clinical_trial_search/processors/llm_tagger.py` - LLM processor for trial tagging
- `docker-compose.yml` - Docker Compose configuration for PostgreSQL
- `scripts/load_aact_data.sh` - Script to load AACT data into PostgreSQL
- `AACT_DB.md` - Documentation of the AACT database structure and relevant tables/columns for this project

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
