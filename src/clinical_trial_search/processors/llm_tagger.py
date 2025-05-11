"""Use LLMs to tag and categorize clinical trial data.

This module processes clinical trial information and uses LLMs to:
1. Generate standardized tags for conditions
2. Evaluate eligibility criteria in plain language
3. Assess potential relevance for different patient scenarios
4. Extract key information like phases, mechanisms, etc.
"""

import json
import logging
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Process clinical trial data with LLMs."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-latest",
    ) -> None:
        """Initialize the LLM processor.

        Args:
            api_key: API key for the LLM service
            api_url: URL for the LLM API (not used with official client)
            model: Model to use for processing
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM API using the official Anthropic Python client.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            The LLM response text
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text from response
        content = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                content += block.text
            else:
                logger.debug(f"Skipping non-text block in response: {block}")
        return content

    async def generate_trial_tags(self, trial_data: dict[str, Any]) -> dict[str, Any]:
        """Generate tags and metadata for a clinical trial.

        Args:
            trial_data: Raw clinical trial data

        Returns:
            Trial data with added tags and metadata
        """
        # Extract relevant fields for processing
        trial_info = {
            "nct_id": trial_data.get("NCTId", ""),
            "title": trial_data.get("BriefTitle", ""),
            "official_title": trial_data.get("OfficialTitle", ""),
            "summary": trial_data.get("BriefSummary", ""),
            "description": trial_data.get("DetailedDescription", ""),
            "conditions": trial_data.get("Condition", []),
            "intervention_types": trial_data.get("InterventionType", []),
            "intervention_names": trial_data.get("InterventionName", []),
            "eligibility_criteria": trial_data.get("EligibilityCriteria", ""),
            "phase": trial_data.get("Phase", ""),
            "study_type": trial_data.get("StudyType", ""),
            "status": trial_data.get("OverallStatus", ""),
        }

        prompt = f"""You are an expert in clinical trials, oncology, and medical research. Your task is to analyze the following clinical trial information and generate standardized tags that will make it easier for patients to find relevant trials.

## Clinical Trial Information
NCT ID: {trial_info["nct_id"]}
Title: {trial_info["title"]}
Official Title: {trial_info["official_title"]}
Phase: {trial_info["phase"]}
Status: {trial_info["status"]}

Summary:
{trial_info["summary"]}

Description:
{trial_info["description"]}

Conditions:
{", ".join(trial_info["conditions"]) if isinstance(trial_info["conditions"], list) else trial_info["conditions"]}

Intervention Types:
{", ".join(trial_info["intervention_types"]) if isinstance(trial_info["intervention_types"], list) else trial_info["intervention_types"]}

Intervention Names:
{", ".join(trial_info["intervention_names"]) if isinstance(trial_info["intervention_names"], list) else trial_info["intervention_names"]}

Eligibility Criteria:
{trial_info["eligibility_criteria"]}

## Task
Based on this information, provide the following in JSON format:

1. Standardized condition tags (normalize different terms for the same condition)
2. Categorize the trial by primary mechanism (e.g., immunotherapy, targeted therapy, chemotherapy)
3. Simplified eligibility summary (in plain language bullets)
4. Key inclusion criteria tags (e.g., "no prior treatment", "recurrent disease")
5. Key exclusion criteria tags (e.g., "brain metastases", "autoimmune disease")
6. Treatment target tags (e.g., specific genes, proteins, pathways)
7. Assign a relevance score (1-5) for each stage of disease (early, locally advanced, recurrent/metastatic)

Your response should ONLY be properly formatted JSON with these fields.
"""  # noqa

        response = await self._call_llm(prompt)

        # Extract JSON from the response
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                tags_data = json.loads(json_str)
            else:
                # Fallback if no JSON found
                tags_data = {"error": "Could not extract JSON from LLM response"}
                logger.error(f"Could not extract JSON from LLM response: {response}")
        except json.JSONDecodeError:
            tags_data = {"error": "Failed to parse JSON from LLM response"}
            logger.error(f"Failed to parse JSON from LLM response: {response}")

        # Merge original data with the new tags
        result = trial_data.copy()
        result["llm_generated_tags"] = tags_data

        return result

    async def process_trials_batch(
        self, trials: list[dict[str, Any]], output_file: str | Path | None = None
    ) -> list[dict[str, Any]]:
        """Process a batch of clinical trials.

        Args:
            trials: List of trial data to process
            output_file: Optional path to save results

        Returns:
            List of processed trial data with tags
        """
        results = []

        # Process each trial
        for trial in trials:
            logger.info(f"Processing trial {trial.get('NCTId', 'unknown')}")
            processed_trial = await self.generate_trial_tags(trial)
            results.append(processed_trial)

        # Save results if output file specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Saved processed results to {output_path}")

        return results
