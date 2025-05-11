# Clinical Trial Search

A tool to help patients find clinical trials relevant to their conditions using LLMs to analyze trial information and generate accurate search tags.

## Problem

Finding relevant clinical trials is incredibly difficult for patients:

- Existing trial databases like ClinicalTrials.gov and AACT have limited search functionality
- Trial keywords and terminology are inconsistent
- Evaluating trial promise requires specialized medical knowledge
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

To download the latest clinical trial dataset from AACT:

```bash
./scripts/download_trials.py
```

For testing without downloading the large dataset:

```bash
./scripts/download_trials.py --test-mode
```

For more options:

```bash
./scripts/download_trials.py --help
```

### Process Trials with LLM

Set your API key for the LLM service:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

Process downloaded trials:

```bash
./scripts/process_trials.py --input-file data/raw/aact_dataset_20250511.zip
```

You can process a subset of trials for testing:

```bash
./scripts/process_trials.py --input-file data/raw/aact_dataset_sample_20250511.json --max-trials 5
```

For more options:

```bash
./scripts/process_trials.py --help
```

### Understanding the LLM-Generated Tags

The LLM processor analyzes each trial and generates the following tags:

1. **Standardized condition tags**: Normalized terms for the same conditions
2. **Mechanism categorization**: Categorizes the trial by primary mechanism (e.g., immunotherapy)
3. **Simplified eligibility summary**: Plain language bullets of eligibility criteria
4. **Inclusion criteria tags**: Key inclusion criteria (e.g., "no prior treatment")
5. **Exclusion criteria tags**: Key exclusion criteria (e.g., "brain metastases")
6. **Treatment target tags**: Specific genes, proteins, or pathways targeted
7. **Relevance scores**: Scores from 1-5 for different disease stages

## Architecture

- `src/clinical_trial_search/downloaders/`: Download clinical trial data
- `src/clinical_trial_search/processors/`: Process and analyze trial data with LLMs
- `scripts/`: Command-line utilities

## Future Roadmap

- Web interface for searching processed trials
- Database storage for tagged trials
- Enhanced LLM prompts for better tagging accuracy
- Patient-specific matching against eligibility criteria
- Integration with other clinical trial sources
- Trial relevance ranking based on patient profiles

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Development Status

Currently in early development.