#!/usr/bin/env python
"""Script to download clinical trial data from AACT."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.clinical_trial_search.downloaders.aact import AACTDownloader
from src.clinical_trial_search.utils.logging import setup_colored_logging


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration with colored output.

    Args:
        verbose: Whether to enable verbose logging
    """
    setup_colored_logging(verbose)


async def main() -> None:
    """Run the AACT clinical trial data downloader."""
    parser = argparse.ArgumentParser(description="Download clinical trial data from AACT")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Directory to store downloaded data (default: ./data)",
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
    downloader = AACTDownloader(data_dir)
    logger.info("Starting download of latest AACT dataset")
    output_file = await downloader.download_latest_dataset()
    logger.info(f"AACT dataset downloaded to {output_file}")
    print(f"\nSuccessfully downloaded AACT dataset to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
