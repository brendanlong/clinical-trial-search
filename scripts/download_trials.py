#!/usr/bin/env python
"""Script to download clinical trial data from ClinicalTrials.gov."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.clinical_trial_search.downloaders.clinicaltrials_gov import ClinicalTrialsGovDownloader


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
    """Run the clinical trial downloader."""
    parser = argparse.ArgumentParser(
        description="Download clinical trial data from ClinicalTrials.gov"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Directory to store downloaded data (default: ./data)",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Search query for clinical trials (e.g., 'cancer')",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of results to return (default: 100)",
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Download bulk data instead of searching",
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

    data_dir = Path(args.data_dir)
    downloader = ClinicalTrialsGovDownloader(data_dir)

    if args.bulk:
        logger.info("Starting bulk download")
        output_file = await downloader.download_bulk_data()
        logger.info(f"Bulk data downloaded to {output_file}")
    elif args.query:
        logger.info(f"Searching for trials with query: {args.query}")
        results = await downloader.search_trials(
            query=args.query,
            max_results=args.max_results,
        )
        output_file = downloader.save_search_results(results, args.query)
        logger.info(f"Search results saved to {output_file}")

        # Print summary
        conditions = set()
        phases = set()
        statuses = set()

        for trial in results:
            if "Condition" in trial:
                if isinstance(trial["Condition"], list):
                    conditions.update(trial["Condition"])
                else:
                    conditions.add(trial["Condition"])

            if "Phase" in trial:
                phases.add(trial["Phase"])

            if "OverallStatus" in trial:
                statuses.add(trial["OverallStatus"])

        print(f"\nFound {len(results)} trials matching '{args.query}'")
        print(f"Phases: {', '.join(sorted(phase for phase in phases if phase))}")
        print(f"Statuses: {', '.join(sorted(status for status in statuses if status))}")
        print(f"Top conditions: {', '.join(sorted(list(conditions)[:10]))}")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
