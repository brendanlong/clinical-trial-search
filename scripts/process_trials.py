#!/usr/bin/env python
"""Script to process clinical trial data with LLMs."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.clinical_trial_search.processors.llm_tagger import LLMProcessor


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


async def main() -> None:
    """Run the clinical trial processor."""
    parser = argparse.ArgumentParser(description="Process clinical trial data with LLMs")
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Input JSON file with clinical trial data",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file for processed data (default: input_file with _processed suffix)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="API key for the LLM service (default: ANTHROPIC_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-3-sonnet-20240229",
        help="Model to use for processing (default: claude-3-sonnet-20240229)",
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Maximum number of trials to process (default: all)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    if not args.api_key:
        logger.error(
            "API key is required. Set ANTHROPIC_API_KEY environment variable or use --api-key"
        )
        sys.exit(1)

    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Default output file is input file with _processed suffix
    if not args.output_file:
        output_path = input_path.with_stem(f"{input_path.stem}_processed")
    else:
        output_path = Path(args.output_file)

    # Initialize processor
    processor = LLMProcessor(
        api_key=args.api_key,
        model=args.model,
    )

    # Load input data
    with open(input_path) as f:
        data = json.load(f)

    # Extract trials from the data structure
    if isinstance(data, dict) and "results" in data:
        trials = data["results"]
    elif isinstance(data, list):
        trials = data
    else:
        logger.error(
            "Invalid input data format. Expected list of trials or dict with 'results' key"
        )
        sys.exit(1)

    if args.max_trials:
        trials = trials[: args.max_trials]
        logger.info(f"Processing {len(trials)} trials (limited by --max-trials)")
    else:
        logger.info(f"Processing {len(trials)} trials")

    # Process the trials
    processed_trials = await processor.process_trials_batch(trials, output_path)

    logger.info(f"Processed {len(processed_trials)} trials")
    logger.info(f"Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
