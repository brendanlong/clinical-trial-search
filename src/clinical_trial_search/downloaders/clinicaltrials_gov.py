"""Downloader for ClinicalTrials.gov data.

ClinicalTrials.gov offers several ways to access data:
1. API: https://clinicaltrials.gov/api/
2. Bulk downloads: https://clinicaltrials.gov/data-api/

This module implements methods to download and parse this data.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

API_BASE_URL = "https://clinicaltrials.gov/api/v2"
BULK_DATA_URL = "https://clinicaltrials.gov/api/bulk/json/studies"


class ClinicalTrialsGovDownloader:
    """Downloader for ClinicalTrials.gov data."""

    def __init__(self, data_dir: str | Path) -> None:
        """Initialize the downloader.

        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)

    async def download_bulk_data(self) -> Path:
        """Download the full bulk data export from ClinicalTrials.gov.

        Returns:
            Path to the downloaded file
        """
        logger.info("Downloading bulk data from ClinicalTrials.gov")
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = self.raw_dir / f"clinicaltrials_gov_bulk_{date_str}.zip"

        if output_file.exists():
            logger.info(f"Found existing bulk data at {output_file}")
            return output_file

        async with httpx.AsyncClient() as client:
            response = await client.get(BULK_DATA_URL, follow_redirects=True)
            response.raise_for_status()

            # Stream to file to handle large download
            with open(output_file, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        logger.info(f"Bulk data downloaded to {output_file}")
        return output_file

    async def search_trials(
        self,
        query: str,
        fields: list[str] | None = None,
        max_results: int = 100,
    ) -> list[dict]:
        """Search for clinical trials using the API.

        Args:
            query: Search query
            fields: Specific fields to return
            max_results: Maximum number of results to return

        Returns:
            List of trial data dictionaries
        """
        if fields is None:
            fields = [
                "NCTId",
                "BriefTitle",
                "OfficialTitle",
                "BriefSummary",
                "DetailedDescription",
                "Condition",
                "InterventionType",
                "InterventionName",
                "EligibilityCriteria",
                "Phase",
                "StudyType",
                "OverallStatus",
                "StartDate",
                "PrimaryCompletionDate",
                "LocationFacility",
                "LocationCity",
                "LocationState",
                "LocationCountry",
            ]

        params = {
            "query.term": query,
            "pageSize": min(1000, max_results),  # API limit is 1000
            "fields": ",".join(fields),
            "format": "json",
        }

        results = []
        page = 1
        total_count = None

        async with httpx.AsyncClient() as client:
            while len(results) < max_results:
                params["page"] = page
                logger.info(f"Fetching page {page} of search results")

                response = await client.get(f"{API_BASE_URL}/studies", params=params)
                response.raise_for_status()

                data = response.json()
                studies = data.get("studies", [])

                if not studies:
                    break

                results.extend(studies)

                # Update total count if not set
                if total_count is None:
                    total_count = data.get("totalCount", 0)
                    logger.info(f"Found {total_count} total results")

                page += 1

                # Break if we've reached the end
                if len(results) >= total_count or len(results) >= max_results:
                    break

        logger.info(f"Retrieved {len(results)} studies")
        return results[:max_results]

    def save_search_results(self, results: list[dict], query: str) -> Path:
        """Save search results to a file.

        Args:
            results: List of trial data
            query: The original search query

        Returns:
            Path to the saved file
        """
        date_str = datetime.now().strftime("%Y%m%d")
        # Create a safe filename from the query
        safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
        output_file = self.raw_dir / f"search_{safe_query}_{date_str}.json"

        with open(output_file, "w") as f:
            json.dump(
                {"query": query, "timestamp": datetime.now().isoformat(), "results": results},
                f,
                indent=2,
            )

        logger.info(f"Saved {len(results)} search results to {output_file}")
        return output_file
