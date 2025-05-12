"""PostgreSQL database connector for clinical trial search."""

import asyncio
import json
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

    async def find_unprocessed_trials(self, limit: int = 10) -> list[dict[str, Any]]:
        """Find multiple clinical trials that haven't been processed yet.

        Args:
            limit: Maximum number of trials to return

        Returns:
            A list of dictionaries with trial data
        """
        async with self.acquire() as conn:
            # Get all trial data in a single query using JSON aggregation
            studies = await conn.fetch(
                """
                SELECT
                    s.nct_id,
                    s.brief_title,
                    s.official_title,
                    s.phase,
                    s.overall_status,
                    s.study_type,
                    bs.description as brief_summary,
                    dd.description as detailed_description,
                    (
                        SELECT jsonb_agg(c.name)
                        FROM ctgov.conditions c
                        WHERE c.nct_id = s.nct_id
                    ) as conditions,
                    (
                        SELECT jsonb_agg(jsonb_build_object(
                            'intervention_type', i.intervention_type,
                            'name', i.name,
                            'description', i.description
                        ))
                        FROM ctgov.interventions i
                        WHERE i.nct_id = s.nct_id
                    ) as interventions,
                    (
                        SELECT jsonb_build_object(
                            'criteria', e.criteria,
                            'gender', e.gender,
                            'minimum_age', e.minimum_age,
                            'maximum_age', e.maximum_age
                        )
                        FROM ctgov.eligibilities e
                        WHERE e.nct_id = s.nct_id
                    ) as eligibility
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
                    AND s.completion_date IS NULL
                LIMIT $1
                """,
                limit,
            )

            if not studies:
                return []

            result = []
            for study in studies:
                study_dict = dict(study)

                # Parse JSON fields from PostgreSQL
                if study_dict["conditions"] is None:
                    study_dict["conditions"] = []
                else:
                    study_dict["conditions"] = json.loads(study_dict["conditions"])

                if study_dict["interventions"] is None:
                    study_dict["interventions"] = []
                else:
                    study_dict["interventions"] = json.loads(study_dict["interventions"])

                if study_dict["eligibility"] is None:
                    study_dict["eligibility"] = {}
                else:
                    study_dict["eligibility"] = json.loads(study_dict["eligibility"])

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
