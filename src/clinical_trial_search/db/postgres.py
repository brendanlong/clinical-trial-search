"""PostgreSQL database connector for clinical trial search."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class PostgresConnector:
    """PostgreSQL connector for clinical trial search database operations."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        database: str = "aact",
        min_connections: int = 1,
        max_connections: int = 10,
    ) -> None:
        """Initialize the PostgreSQL connector.

        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            min_connections: Minimum number of connections in the pool
            max_connections: Maximum number of connections in the pool
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: Pool | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Create the connection pool if it doesn't exist."""
        if self._pool is not None:
            return

        async with self._lock:
            # Check again in case another task created the pool while we were waiting
            if self._pool is not None:
                return

            logger.info(f"Connecting to PostgreSQL at {self.host}:{self.port}/{self.database}")
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=self.min_connections,
                max_size=self.max_connections,
            )
            logger.info("Connection pool created successfully")

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            logger.info("Closing PostgreSQL connection pool")
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool.

        Yields:
            An asyncpg connection
        """
        if self._pool is None:
            await self.connect()

        if self._pool is None:
            raise RuntimeError("Failed to create connection pool")

        async with self._pool.acquire() as conn:
            yield conn

    async def find_unprocessed_trial(self) -> dict[str, Any] | None:
        """Find a single clinical trial that hasn't been processed yet.

        This method finds trials that exist in the ctgov.studies table but not in
        the ctsearch.processed_trials table.

        Returns:
            A dictionary with trial data or None if no unprocessed trials are found
        """
        async with self.acquire() as conn:
            # Find one trial that hasn't been processed yet
            study = await conn.fetchrow(
                """
                SELECT
                    s.nct_id,
                    s.brief_title,
                    s.official_title,
                    s.phase,
                    s.overall_status,
                    s.study_type,
                    bs.description as brief_summary,
                    dd.description as detailed_description
                FROM
                    ctgov.studies s
                LEFT JOIN
                    ctgov.brief_summaries bs ON s.nct_id = bs.nct_id
                LEFT JOIN
                    ctgov.detailed_descriptions dd ON s.nct_id = dd.nct_id
                LEFT JOIN
                    ctsearch.processed_trials pt ON s.nct_id = pt.nct_id
                WHERE
                    pt.nct_id IS NULL
                LIMIT 1
                """
            )

            if not study:
                return None

            # Get condition data
            conditions = await conn.fetch(
                """
                SELECT name
                FROM ctgov.conditions
                WHERE nct_id = $1
                """,
                study["nct_id"],
            )

            # Get intervention data
            interventions = await conn.fetch(
                """
                SELECT intervention_type, name, description
                FROM ctgov.interventions
                WHERE nct_id = $1
                """,
                study["nct_id"],
            )

            # Get eligibility criteria
            eligibility = await conn.fetchrow(
                """
                SELECT criteria, gender, minimum_age, maximum_age
                FROM ctgov.eligibilities
                WHERE nct_id = $1
                """,
                study["nct_id"],
            )

            # Convert row objects to dictionaries
            study_dict = dict(study)

            # Add related data
            study_dict["conditions"] = [c["name"] for c in conditions]
            study_dict["interventions"] = [dict(i) for i in interventions]
            study_dict["eligibility"] = dict(eligibility) if eligibility else {}

            return study_dict

    async def find_unprocessed_trials(self, limit: int = 10) -> list[dict[str, Any]]:
        """Find multiple clinical trials that haven't been processed yet.

        Args:
            limit: Maximum number of trials to return

        Returns:
            A list of dictionaries with trial data
        """
        async with self.acquire() as conn:
            # Find trials that haven't been processed yet
            studies = await conn.fetch(
                """
                SELECT
                    s.nct_id,
                    s.brief_title,
                    s.official_title,
                    s.phase,
                    s.overall_status,
                    s.study_type
                FROM
                    ctgov.studies s
                LEFT JOIN
                    ctsearch.processed_trials pt ON s.nct_id = pt.nct_id
                WHERE
                    pt.nct_id IS NULL
                LIMIT $1
                """,
                limit,
            )

            if not studies:
                return []

            result = []
            for study in studies:
                study_dict = dict(study)

                # Get brief summary
                brief_summary = await conn.fetchrow(
                    """
                    SELECT description
                    FROM ctgov.brief_summaries
                    WHERE nct_id = $1
                    """,
                    study["nct_id"],
                )
                if brief_summary:
                    study_dict["brief_summary"] = brief_summary["description"]

                # Get detailed description
                detailed_desc = await conn.fetchrow(
                    """
                    SELECT description
                    FROM ctgov.detailed_descriptions
                    WHERE nct_id = $1
                    """,
                    study["nct_id"],
                )
                if detailed_desc:
                    study_dict["detailed_description"] = detailed_desc["description"]

                # Get condition data
                conditions = await conn.fetch(
                    """
                    SELECT name
                    FROM ctgov.conditions
                    WHERE nct_id = $1
                    """,
                    study["nct_id"],
                )
                study_dict["conditions"] = [c["name"] for c in conditions]

                # Get intervention data
                interventions = await conn.fetch(
                    """
                    SELECT intervention_type, name, description
                    FROM ctgov.interventions
                    WHERE nct_id = $1
                    """,
                    study["nct_id"],
                )
                study_dict["interventions"] = [dict(i) for i in interventions]

                # Get eligibility criteria
                eligibility = await conn.fetchrow(
                    """
                    SELECT criteria, gender, minimum_age, maximum_age
                    FROM ctgov.eligibilities
                    WHERE nct_id = $1
                    """,
                    study["nct_id"],
                )
                if eligibility:
                    study_dict["eligibility"] = dict(eligibility)

                result.append(study_dict)

            return result

    async def mark_trial_processed(
        self, nct_id: str, success: bool = True, processing_version: int = 1
    ) -> None:
        """Mark a trial as processed in the database.

        Args:
            nct_id: The NCT ID of the processed trial
            success: Whether processing was successful
            processing_version: The version of the processing algorithm used
        """
        async with self.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ctsearch.processed_trials
                (nct_id, successfully_processed, processing_version)
                VALUES ($1, $2, $3)
                ON CONFLICT (nct_id)
                DO UPDATE SET
                    processed_at = CURRENT_TIMESTAMP,
                    successfully_processed = $2,
                    processing_version = $3
                """,
                nct_id,
                success,
                processing_version,
            )

    async def save_trial_tags(self, nct_id: str, tags_data: dict[str, Any]) -> None:
        """Save LLM-generated tags for a clinical trial.

        Args:
            nct_id: The NCT ID of the trial
            tags_data: The tags data generated by the LLM
        """
        async with self.acquire() as conn:
            async with conn.transaction():
                # 1. Insert condition tags
                if "condition_tags" in tags_data:
                    for condition in tags_data["condition_tags"]:
                        # First ensure the condition exists in condition_tags table
                        condition_id = await conn.fetchval(
                            """
                            INSERT INTO ctsearch.condition_tags (condition_name)
                            VALUES ($1)
                            ON CONFLICT (condition_name) DO UPDATE SET condition_name = $1
                            RETURNING id
                            """,
                            condition,
                        )

                        # Then link it to the trial with relevance score
                        relevance = 5  # Default high relevance
                        await conn.execute(
                            """
                            INSERT INTO ctsearch.trial_conditions
                            (nct_id, condition_id, relevance_score)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (nct_id, condition_id) DO UPDATE SET
                            relevance_score = $3
                            """,
                            nct_id,
                            condition_id,
                            relevance,
                        )

                # 2. Insert mechanism categories
                if "mechanisms" in tags_data:
                    for mechanism in tags_data["mechanisms"]:
                        # First ensure the mechanism exists in mechanism_categories table
                        mechanism_id = await conn.fetchval(
                            """
                            INSERT INTO ctsearch.mechanism_categories (mechanism_name)
                            VALUES ($1)
                            ON CONFLICT (mechanism_name) DO UPDATE SET mechanism_name = $1
                            RETURNING id
                            """,
                            mechanism,
                        )

                        # Then link it to the trial with relevance score
                        relevance = 5  # Default high relevance
                        await conn.execute(
                            """
                            INSERT INTO ctsearch.trial_mechanisms
                            (nct_id, mechanism_id, relevance_score)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (nct_id, mechanism_id) DO UPDATE SET
                            relevance_score = $3
                            """,
                            nct_id,
                            mechanism_id,
                            relevance,
                        )

                # 3. Insert treatment targets
                if "treatment_targets" in tags_data:
                    for target in tags_data["treatment_targets"]:
                        # First ensure the target exists in treatment_targets table
                        # For simplicity, not setting target_type here
                        target_id = await conn.fetchval(
                            """
                            INSERT INTO ctsearch.treatment_targets (target_name)
                            VALUES ($1)
                            ON CONFLICT (target_name) DO UPDATE SET target_name = $1
                            RETURNING id
                            """,
                            target,
                        )

                        # Then link it to the trial
                        await conn.execute(
                            """
                            INSERT INTO ctsearch.trial_targets
                            (nct_id, target_id)
                            VALUES ($1, $2)
                            ON CONFLICT (nct_id, target_id) DO NOTHING
                            """,
                            nct_id,
                            target_id,
                        )

                # 4. Insert simplified eligibility
                if "simplified_eligibility" in tags_data:
                    await conn.execute(
                        """
                        INSERT INTO ctsearch.simplified_eligibility
                        (nct_id, summary)
                        VALUES ($1, $2)
                        ON CONFLICT (nct_id) DO UPDATE SET
                        summary = $2
                        """,
                        nct_id,
                        tags_data["simplified_eligibility"],
                    )

                # 5. Insert inclusion criteria
                if "inclusion_criteria" in tags_data:
                    for criteria in tags_data["inclusion_criteria"]:
                        # First ensure the criteria exists in criteria_tags table
                        criteria_id = await conn.fetchval(
                            """
                            INSERT INTO ctsearch.criteria_tags (criteria_name, criteria_type)
                            VALUES ($1, 'inclusion')
                            ON CONFLICT (criteria_name, criteria_type) DO UPDATE SET
                            criteria_name = $1
                            RETURNING id
                            """,
                            criteria,
                        )

                        # Then link it to the trial
                        await conn.execute(
                            """
                            INSERT INTO ctsearch.trial_criteria
                            (nct_id, criteria_id)
                            VALUES ($1, $2)
                            ON CONFLICT (nct_id, criteria_id) DO NOTHING
                            """,
                            nct_id,
                            criteria_id,
                        )

                # 6. Insert exclusion criteria
                if "exclusion_criteria" in tags_data:
                    for criteria in tags_data["exclusion_criteria"]:
                        # First ensure the criteria exists in criteria_tags table
                        criteria_id = await conn.fetchval(
                            """
                            INSERT INTO ctsearch.criteria_tags (criteria_name, criteria_type)
                            VALUES ($1, 'exclusion')
                            ON CONFLICT (criteria_name, criteria_type) DO UPDATE SET
                            criteria_name = $1
                            RETURNING id
                            """,
                            criteria,
                        )

                        # Then link it to the trial
                        await conn.execute(
                            """
                            INSERT INTO ctsearch.trial_criteria
                            (nct_id, criteria_id)
                            VALUES ($1, $2)
                            ON CONFLICT (nct_id, criteria_id) DO NOTHING
                            """,
                            nct_id,
                            criteria_id,
                        )

                # 7. Insert disease stage relevance
                if "stage_relevance" in tags_data:
                    for stage, score in tags_data["stage_relevance"].items():
                        # First get the stage ID (assuming stages were pre-inserted)
                        stage_id = await conn.fetchval(
                            """
                            SELECT id FROM ctsearch.disease_stages
                            WHERE stage_name = $1
                            """,
                            stage,
                        )

                        if stage_id:
                            # Then link it to the trial with relevance score
                            await conn.execute(
                                """
                                INSERT INTO ctsearch.trial_stage_relevance
                                (nct_id, stage_id, relevance_score)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (nct_id, stage_id) DO UPDATE SET
                                relevance_score = $3
                                """,
                                nct_id,
                                stage_id,
                                score,
                            )
