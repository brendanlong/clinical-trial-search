# Clinical Trial Search

A tool to help patients find clinical trials relevant to their conditions using LLMs to analyze trial information and generate accurate search tags.

## Problem

Finding relevant clinical trials is incredibly difficult for patients:

- ClinicalTrials.gov has poor search functionality
- Trial keywords are inconsistent
- Evaluating trial promise requires specialized knowledge
- Eligibility criteria are complex and unique to each trial

## Solution

This tool aims to:

1. Fetch and process clinical trial data
2. Use LLMs to generate standardized, accurate tags for each trial
3. Create a user-friendly search interface
4. Help patients find the most relevant trials for their specific condition

## Installation

1. Clone this repository
2. Create a virtual environment with uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install the package:
   ```bash
   uv pip install -e '.[dev]'
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Usage

### Download Clinical Trial Data

To search for clinical trials:

```bash
./scripts/download_trials.py --query "head and neck cancer" --max-results 100
```

To download the bulk data:

```bash
./scripts/download_trials.py --bulk
```

### Process Trials with LLM

Set your API key for the LLM service:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

Process downloaded trials:

```bash
./scripts/process_trials.py --input-file data/raw/search_head_and_neck_cancer_20250511.json
```

## Architecture

- `src/clinical_trial_search/downloaders/`: Download clinical trial data
- `src/clinical_trial_search/processors/`: Process and analyze trial data with LLMs
- `scripts/`: Command-line utilities

## Development Status

Currently in early development.