# File: deep_research.py | Module: mcp-server
"""Gemini Deep Research client using the Interactions API."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from google import genai
from google.genai import types

from config import config
from logger import logger
from models import (
    ResearchResult,
    ResearchResultMetadata,
    ResearchResultSource,
    ResearchSpec,
    ResearchStartResponse,
    ResearchStatus,
    ResearchStatusResponse,
)


class ResearchJob:
    """Tracks a running research job."""

    def __init__(self, job_id: str, spec: ResearchSpec, interaction_id: str) -> None:
        self.job_id = job_id
        self.spec = spec
        self.interaction_id = interaction_id
        self.started_at = datetime.now()
        self.status = ResearchStatus.RUNNING
        self.progress = 0
        self.message = "Starting research..."
        self.result: ResearchResult | None = None
        self.error: str | None = None


class DeepResearchClient:
    """Client for Gemini Deep Research using Interactions API."""

    def __init__(self) -> None:
        """Initialize the deep research client."""
        self.client = genai.Client(api_key=config.google_api_key)
        self._jobs: dict[str, ResearchJob] = {}

    def _build_research_query(self, spec: ResearchSpec) -> str:
        """Build the research query from spec."""
        parts = [spec.research_goal]

        if spec.focus_areas:
            parts.append(f"Focus on: {', '.join(spec.focus_areas[:5])}")

        if spec.domain:
            parts.append(f"Domain: {spec.domain}")

        if spec.constraints.recency == "recent":
            parts.append("Focus on recent developments (2024-2025)")
        elif spec.constraints.recency == "last_year":
            parts.append("Focus on 2024")

        if spec.exclusions:
            parts.append(f"Exclude: {', '.join(spec.exclusions[:3])}")

        return ". ".join(parts)

    async def _start_interaction(self, spec: ResearchSpec) -> str:
        """Start a Deep Research interaction and return the interaction ID."""
        query = self._build_research_query(spec)
        logger.api_call("interactions", "create", agent=config.deep_research_model, query=query[:100])

        try:
            import time
            start_time = time.time()

            # Use Interactions API for Deep Research agent
            interaction = await self.client.aio.interactions.create(
                agent=config.deep_research_model,
                input=query,
                config=types.InteractionConfig(
                    background=True,  # Required for Deep Research
                ),
            )

            duration_ms = (time.time() - start_time) * 1000
            logger.api_response("interactions", "create", duration_ms, success=True)
            logger.debug(f"Started interaction: {interaction.id}")

            return interaction.id

        except Exception as e:
            logger.error(f"Failed to start interaction: {e}")
            raise

    async def _poll_interaction(self, job: ResearchJob) -> None:
        """Poll the interaction until complete."""
        logger.phase_start("Deep Research", f"job_id={job.job_id}, interaction_id={job.interaction_id}")

        try:
            poll_count = 0
            max_polls = config.research_timeout // config.poll_interval

            while poll_count < max_polls:
                poll_count += 1

                # Get interaction status
                interaction = await self.client.aio.interactions.get(
                    id=job.interaction_id,
                )

                # Check if done
                if interaction.done:
                    logger.debug(f"Interaction complete after {poll_count} polls")
                    break

                # Update progress (estimate based on poll count)
                job.progress = min(85, int((poll_count / max_polls) * 85))
                job.message = "Researching..."
                logger.progress("Research", job.progress, f"Poll {poll_count}")

                await asyncio.sleep(config.poll_interval)

            # Get final result
            interaction = await self.client.aio.interactions.get(
                id=job.interaction_id,
            )

            if not interaction.done:
                raise TimeoutError("Research timed out")

            # Extract report from interaction output
            report = ""
            sources: list[ResearchResultSource] = []

            if interaction.output:
                report = interaction.output
            elif interaction.messages:
                # Get last assistant message
                for msg in reversed(interaction.messages):
                    if msg.role == "assistant" and msg.content:
                        report = msg.content
                        break

            # Extract sources from grounding metadata if available
            if hasattr(interaction, 'grounding_metadata') and interaction.grounding_metadata:
                grounding = interaction.grounding_metadata
                if hasattr(grounding, 'grounding_chunks'):
                    for chunk in grounding.grounding_chunks or []:
                        if hasattr(chunk, 'web') and chunk.web:
                            sources.append(ResearchResultSource(
                                title=chunk.web.title or "Untitled",
                                url=chunk.web.uri or "",
                            ))

            elapsed = (datetime.now() - job.started_at).total_seconds()

            job.result = ResearchResult(
                report=report,
                sources=sources[:20],
                metadata=ResearchResultMetadata(
                    duration_seconds=elapsed,
                    sources_analyzed=len(sources),
                ),
            )
            job.progress = 100
            job.status = ResearchStatus.COMPLETE
            job.message = "Research complete"
            logger.phase_end("Deep Research", success=True, details=f"report={len(report)} chars, sources={len(sources)}")

        except Exception as e:
            job.status = ResearchStatus.FAILED
            job.error = str(e)
            job.message = f"Research failed: {str(e)}"
            logger.phase_end("Deep Research", success=False, details=str(e))
            logger.exception("Research pipeline failed")

    async def start(self, spec: dict[str, Any]) -> ResearchStartResponse:
        """Start an async deep research job using Interactions API."""
        try:
            research_spec = ResearchSpec(**spec)
        except Exception as e:
            raise ValueError(f"Invalid research spec: {e}")

        # Start the interaction
        interaction_id = await self._start_interaction(research_spec)

        job_id = f"research-{uuid.uuid4().hex[:12]}"
        job = ResearchJob(job_id, research_spec, interaction_id)
        self._jobs[job_id] = job

        # Start polling in background
        asyncio.create_task(self._poll_interaction(job))

        return ResearchStartResponse(
            job_id=job_id,
            status="started",
            estimated_time_seconds=config.research_timeout,
        )

    async def check_status(self, job_id: str) -> ResearchStatusResponse:
        """Check the status of a research job."""
        job = self._jobs.get(job_id)

        if not job:
            return ResearchStatusResponse(
                status=ResearchStatus.FAILED,
                progress=0,
                message="Job not found",
            )

        return ResearchStatusResponse(
            status=job.status,
            progress=job.progress,
            message=job.message,
        )

    async def get_result(self, job_id: str) -> ResearchResult:
        """Get the result of a completed research job."""
        job = self._jobs.get(job_id)

        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Wait for completion if still running
        while job.status == ResearchStatus.RUNNING:
            await asyncio.sleep(1)

        if job.status == ResearchStatus.FAILED:
            raise ValueError(f"Research failed: {job.error}")

        if not job.result:
            raise ValueError(f"Job {job_id} has no result")

        return job.result
