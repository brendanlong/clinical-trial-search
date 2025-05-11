"""Downloader for AACT clinical trial data.

AACT (Aggregate Analysis of ClinicalTrials.gov) provides static database copies
at https://aact.ctti-clinicaltrials.org/download. This module implements
methods to download these static copies.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from tqdm import tqdm

logger = logging.getLogger(__name__)

AACT_BASE_URL = "https://aact.ctti-clinicaltrials.org"
DOWNLOAD_PAGE_URL = f"{AACT_BASE_URL}/download"


class AACTDownloader:
    """Downloader for AACT clinical trial data."""

    def __init__(self, data_dir: str | Path) -> None:
        """Initialize the downloader.

        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)

    async def get_latest_dataset_url(self) -> str:
        """Find the URL for the latest daily dataset.

        Returns:
            URL for the latest dataset
        """
        logger.info("Fetching AACT download page to find latest dataset")

        async with httpx.AsyncClient() as client:
            response = await client.get(DOWNLOAD_PAGE_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Find the select element for "Current Month's Daily Static Copies"
            select_elements = soup.find_all("select", {"class": "form-select"})
            if not select_elements or len(select_elements) < 1:
                raise ValueError("Could not find dataset select element on AACT download page")

            # Get the first option (after the placeholder)
            daily_select = select_elements[0]
            # Type check to ensure it's a Tag with find_all method
            if not isinstance(daily_select, Tag):
                raise ValueError("Select element is not a Tag")
            options = daily_select.find_all("option")

            # Skip the first option which is just placeholder text
            if len(options) < 2:
                raise ValueError("No dataset options found on AACT download page")

            latest_option = options[1]
            if not isinstance(latest_option, Tag):
                raise ValueError("Option element is not a Tag")
            dataset_path = latest_option.get("value")

            if not dataset_path:
                raise ValueError("Could not extract dataset path from option")

            # Dataset URL will be like /static/static_db_copies/daily/2025-05-11
            # Ensure dataset_path is a string for urljoin
            path_str = str(dataset_path)
            full_url = urljoin(AACT_BASE_URL, path_str)
            logger.info(f"Found latest dataset URL: {full_url}")

            return full_url

    async def get_dataset_filename(self, dataset_url: str) -> str:
        """Extract the expected filename from a dataset URL.

        Args:
            dataset_url: URL for the dataset

        Returns:
            Expected filename for the dataset
        """
        # Extract date from URL which is typically like /static/static_db_copies/daily/2025-05-11
        date_match = re.search(r"/daily/(\d{4}-\d{2}-\d{2})$", dataset_url)
        if not date_match:
            raise ValueError(f"Could not extract date from dataset URL: {dataset_url}")

        date_str = date_match.group(1).replace("-", "")
        filename = f"{date_str}_clinical_trials_ctgov.zip"

        return filename

    async def _download_file(self, client: httpx.AsyncClient, url: str, output_file: Path) -> None:
        """Download a file with progress tracking.

        Args:
            client: HTTP client to use for the request
            url: URL to download from
            output_file: Local file path to save to
        """
        logger.info(f"Downloading file from {url}")
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

        # Get the total size if available for progress bar
        total_size = int(response.headers.get("content-length", 0))
        with open(output_file, "wb") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"Downloading {output_file.name}",
            ) as progress_bar:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    progress_bar.update(len(chunk))

    async def download_latest_dataset(self) -> Path:
        """Download the latest dataset from AACT.

        Returns:
            Path to the downloaded file
        """
        logger.info("Downloading latest dataset from AACT")

        # Get today's date for the output filename
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = self.raw_dir / f"aact_dataset_{date_str}.zip"

        if output_file.exists():
            logger.info(f"Found existing dataset at {output_file}")
            return output_file

        # Get the URL for the latest dataset
        dataset_url = await self.get_latest_dataset_url()
        expected_filename = await self.get_dataset_filename(dataset_url)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(dataset_url, follow_redirects=True)
            response.raise_for_status()

            # If we got redirected to download the file directly,
            # the content should be the zip file
            if response.headers.get("content-type") == "application/zip":
                await self._download_file(client, dataset_url, output_file)
            else:
                # Otherwise, we need to find the download link on the page
                soup = BeautifulSoup(response.text, "html.parser")
                download_link = None

                # Look for a link containing the expected filename
                for link in soup.find_all("a"):
                    if not isinstance(link, Tag):
                        continue
                    href = link.get("href")
                    if href and isinstance(href, str) and expected_filename in href:
                        download_link = href
                        break

                if not download_link:
                    raise ValueError(f"Could not find download link for {expected_filename}")

                # Ensure download_link is a string for urljoin
                link_str = str(download_link)
                file_url = urljoin(AACT_BASE_URL, link_str)
                await self._download_file(client, file_url, output_file)

        logger.info(f"Dataset downloaded to {output_file}")
        return output_file
