# Clinical Trial Search Scripts

This directory contains scripts for setting up, downloading, and processing clinical trial data.

## Setup Scripts

### `setup_ctsearch_db.sh`

Sets up the `ctsearch` schema in the PostgreSQL database, which stores the LLM-processed trial data.

```bash
./setup_ctsearch_db.sh
```

This script:
1. Checks if Docker and the database container are running
2. Verifies the AACT database exists
3. Creates the `ctsearch` schema and tables
4. Verifies the tables were created successfully

The schema is defined in `setup_ctsearch_db.sql` and includes tables for:
- Processed trial tracking
- Condition tags
- Treatment mechanisms
- Treatment targets
- Disease stage relevance
- Simplified eligibility criteria
- Location information

## Data Scripts

### `download_trials.py`

Downloads clinical trial data from the AACT database.

```bash
./download_trials.py [--test-mode] [--output-dir DIR]
```

Options:
- `--test-mode`: Download a small sample instead of the full dataset
- `--output-dir`: Specify where to save the downloaded data

### `load_aact_data.sh`

Loads the downloaded AACT data into a PostgreSQL database using Docker.

```bash
./load_aact_data.sh
```

This script:
1. Starts a PostgreSQL container
2. Extracts the database dump
3. Loads the data into PostgreSQL

### `process_trials.py`

Processes clinical trial data with an LLM to generate tags and structured data.

```bash
./process_trials.py --input-file FILE [--output-file FILE] [--max-trials N]
```

Options:
- `--input-file`: Path to the downloaded trial data
- `--output-file`: Path to save processed results (optional)
- `--max-trials`: Maximum number of trials to process (for testing)

Requires the `ANTHROPIC_API_KEY` environment variable to be set.
