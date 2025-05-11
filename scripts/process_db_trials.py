#!/usr/bin/env python
"""Script to process clinical trials from the database using LLMs."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.clinical_trial_search.db.postgres import PostgresConnector
from src.clinical_trial_search.processors.llm_tagger import LLMProcessor
from src.clinical_trial_search.utils.logging import setup_colored_logging


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration with colored output.

    Args:
        verbose: Whether to enable verbose logging
    """
    setup_colored_logging(verbose)


async def process_trials(
    db_connector: PostgresConnector,
    llm_processor: LLMProcessor,
    batch_size: int = 5,
    max_trials: int = sys.maxsize,
) -> int:
    """Process a batch of unprocessed trials from the database.

    Args:
        db_connector: PostgreSQL database connector
        llm_processor: LLM processor for generating trial tags
        batch_size: Number of trials to process in each batch
        max_trials: Maximum total number of trials to process

    Returns:
        The number of trials processed
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing unprocessed trials (batch size: {batch_size})")

    processed_count = 0
    remaining = max_trials

    while True:
        # Check if we've reached the maximum number of trials
        if processed_count >= max_trials:
            break
        current_batch_size = min(batch_size, remaining)

        # Get a batch of unprocessed trials
        trials = await db_connector.find_unprocessed_trials(limit=current_batch_size)

        if not trials:
            logger.info("No more unprocessed trials found")
            break

        logger.info(f"Found {len(trials)} unprocessed trials")

        # Process each trial in the batch
        for trial in trials:
            nct_id = trial["nct_id"]
            logger.info(f"Processing trial {nct_id}: {trial.get('brief_title', '')}")

            # Convert to format expected by LLM processor
            llm_input = {
                "NCTId": nct_id,
                "BriefTitle": trial.get("brief_title", ""),
                "OfficialTitle": trial.get("official_title", ""),
                "BriefSummary": trial.get("brief_summary", ""),
                "DetailedDescription": trial.get("detailed_description", ""),
                "Phase": trial.get("phase", ""),
                "OverallStatus": trial.get("overall_status", ""),
                "StudyType": trial.get("study_type", ""),
                "Condition": trial.get("conditions", []),
                "InterventionType": [
                    i.get("intervention_type", "") for i in trial.get("interventions", [])
                ],
                "InterventionName": [i.get("name", "") for i in trial.get("interventions", [])],
                "EligibilityCriteria": trial.get("eligibility", {}).get("criteria", ""),
            }

            # Process the trial with LLM
            processed_trial = await llm_processor.generate_trial_tags(llm_input)
            llm_tags = processed_trial.get("llm_generated_tags", {})

            # Check if processing was successful
            success = "error" not in llm_tags

            if success:
                # Save the trial tags to the database
                logger.info(f"Saving tags for trial {nct_id}")
                await db_connector.save_trial_tags(nct_id, llm_tags)
            else:
                logger.error(
                    f"Error processing trial {nct_id}: {llm_tags.get('error', 'Unknown error')}"
                )

            # Mark the trial as processed
            await db_connector.mark_trial_processed(nct_id, success=success)
            processed_count += 1

        if max_trials is not None:
            remaining = max_trials - processed_count

    return processed_count


async def main() -> None:
    """Run the clinical trial processor."""
    parser = argparse.ArgumentParser(
        description="Process clinical trials from the database with LLMs"
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
        default="claude-3-5-haiku-latest",
        help="Model to use for processing (default: claude-3-5-haiku-latest)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of trials to process in each batch (default: 5)",
    )
    parser.add_argument(
        "--max-trials",
        type=int,
        default=None,
        help="Maximum number of trials to process (default: all)",
    )
    parser.add_argument(
        "--db-host",
        type=str,
        default="localhost",
        help="Database host (default: localhost)",
    )
    parser.add_argument(
        "--db-port",
        type=int,
        default=5432,
        help="Database port (default: 5432)",
    )
    parser.add_argument(
        "--db-user",
        type=str,
        default="postgres",
        help="Database user (default: postgres)",
    )
    parser.add_argument(
        "--db-password",
        type=str,
        default="postgres",
        help="Database password (default: postgres)",
    )
    parser.add_argument(
        "--db-name",
        type=str,
        default="aact",
        help="Database name (default: aact)",
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

    # Initialize database connector
    db_connector = PostgresConnector(
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=args.db_password,
        database=args.db_name,
    )

    # Connect to the database
    await db_connector.connect()

    # Initialize LLM processor
    llm_processor = LLMProcessor(
        api_key=args.api_key,
        model=args.model,
    )

    try:
        # Process trials
        processed_count = await process_trials(
            db_connector=db_connector,
            llm_processor=llm_processor,
            batch_size=args.batch_size,
            max_trials=args.max_trials,
        )

        logger.info(f"Processed {processed_count} trials")

    finally:
        # Close database connection
        await db_connector.close()


if __name__ == "__main__":
    asyncio.run(main())
