# File: test_deep_research.py | Module: tests
"""Unit tests for deep_research.py."""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from deep_research import DeepResearchClient, ResearchJob
from models import ResearchSpec, ResearchStatus


class TestResearchJob:
    """Tests for ResearchJob class."""

    def test_job_initialization(self, sample_research_spec):
        """Test job is initialized correctly."""
        spec = ResearchSpec(**sample_research_spec)
        job = ResearchJob("test-123", spec)

        assert job.job_id == "test-123"
        assert job.status == ResearchStatus.RUNNING
        assert job.progress == 0
        assert job.result is None
        assert job.error is None

    def test_job_has_started_at(self, sample_research_spec):
        """Test job has started_at timestamp."""
        spec = ResearchSpec(**sample_research_spec)
        job = ResearchJob("test-123", spec)

        assert isinstance(job.started_at, datetime)


class TestDeepResearchClient:
    """Tests for DeepResearchClient class."""

    @pytest.fixture
    def client(self, mock_genai_client):
        """Create client with mocked genai."""
        with patch("deep_research.genai") as mock_genai:
            mock_genai.Client.return_value = mock_genai_client
            client = DeepResearchClient()
            client.client = mock_genai_client
            return client

    def test_spec_to_research_queries_basic(self, client, sample_research_spec):
        """Test query generation from spec."""
        spec = ResearchSpec(**sample_research_spec)
        queries = client._spec_to_research_queries(spec)

        assert len(queries) > 0
        assert spec.research_goal in queries[0]

    def test_spec_to_research_queries_includes_focus_areas(self, client, sample_research_spec):
        """Test that focus areas are included in queries."""
        spec = ResearchSpec(**sample_research_spec)
        queries = client._spec_to_research_queries(spec)

        # Should have queries for focus areas
        assert any("qubits" in q for q in queries)

    def test_spec_to_research_queries_recency_filter(self, client, sample_research_spec):
        """Test recency filter is applied."""
        sample_research_spec["constraints"]["recency"] = "recent"
        spec = ResearchSpec(**sample_research_spec)
        queries = client._spec_to_research_queries(spec)

        # Recent filter should add year
        assert any("2024" in q or "2025" in q for q in queries)

    def test_spec_to_research_queries_limits_count(self, client, sample_research_spec):
        """Test query count is limited."""
        sample_research_spec["focus_areas"] = ["a", "b", "c", "d", "e", "f", "g", "h"]
        spec = ResearchSpec(**sample_research_spec)
        queries = client._spec_to_research_queries(spec)

        assert len(queries) <= 6

    def test_build_research_prompt(self, client, sample_research_spec):
        """Test prompt building."""
        spec = ResearchSpec(**sample_research_spec)
        prompt = client._build_research_prompt(spec, "test query")

        assert "test query" in prompt
        assert "intermediate" in prompt  # audience level

    @pytest.mark.asyncio
    async def test_start_creates_job(self, client, sample_research_spec):
        """Test start() creates a job and returns response."""
        response = await client.start(sample_research_spec)

        assert response.job_id.startswith("research-")
        assert response.status == "started"
        assert response.job_id in client._jobs

    @pytest.mark.asyncio
    async def test_start_invalid_spec(self, client):
        """Test start() with invalid spec raises error."""
        with pytest.raises(ValueError, match="Invalid research spec"):
            await client.start({})

    @pytest.mark.asyncio
    async def test_check_status_job_not_found(self, client):
        """Test check_status for non-existent job."""
        response = await client.check_status("nonexistent-job")

        assert response.status == ResearchStatus.FAILED
        assert response.message == "Job not found"

    @pytest.mark.asyncio
    async def test_check_status_running_job(self, client, sample_research_spec):
        """Test check_status for running job."""
        # Create a job
        start_response = await client.start(sample_research_spec)
        job = client._jobs[start_response.job_id]
        job.progress = 50
        job.message = "Testing..."

        response = await client.check_status(start_response.job_id)

        assert response.status == ResearchStatus.RUNNING
        assert response.progress == 50

    @pytest.mark.asyncio
    async def test_get_result_job_not_found(self, client):
        """Test get_result for non-existent job."""
        with pytest.raises(ValueError, match="not found"):
            await client.get_result("nonexistent-job")

    @pytest.mark.asyncio
    async def test_get_result_failed_job(self, client, sample_research_spec):
        """Test get_result for failed job."""
        start_response = await client.start(sample_research_spec)
        job = client._jobs[start_response.job_id]
        job.status = ResearchStatus.FAILED
        job.error = "Test error"
        if job._task:
            job._task.cancel()
            try:
                await job._task
            except asyncio.CancelledError:
                pass
        job._task = None

        with pytest.raises(ValueError, match="Research failed"):
            await client.get_result(start_response.job_id)


class TestDeepResearchIntegration:
    """Integration tests for deep research (with mocked API)."""

    @pytest.fixture
    def mock_client(self):
        """Create fully mocked client."""
        with patch("deep_research.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "# Research Report\n\nSample content."
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].grounding_metadata = None

            mock_genai_client = MagicMock()
            mock_genai_client.models.generate_content = MagicMock(return_value=mock_response)
            mock_genai.Client.return_value = mock_genai_client

            with patch("deep_research.config") as mock_config:
                mock_config.google_api_key = "test-key"
                mock_config.deep_research_model = "test-model"
                mock_config.pro_model = "test-pro"
                mock_config.research_timeout = 60

                client = DeepResearchClient()
                client.client = mock_genai_client
                return client

    @pytest.mark.asyncio
    async def test_execute_grounded_query(self, mock_client, sample_research_spec):
        """Test grounded query execution."""
        spec = ResearchSpec(**sample_research_spec)
        content, sources = await mock_client._execute_grounded_query("test query", spec)

        assert "Research Report" in content or "Sample content" in content

    @pytest.mark.asyncio
    async def test_full_research_flow(self, mock_client, sample_research_spec):
        """Test complete research flow with mocked API."""
        # Start research
        start_response = await mock_client.start(sample_research_spec)
        assert start_response.job_id is not None

        # Wait for completion (mocked, should be fast)
        job = mock_client._jobs[start_response.job_id]
        if job._task:
            await asyncio.wait_for(job._task, timeout=10)

        # Check status
        status = await mock_client.check_status(start_response.job_id)
        assert status.status == ResearchStatus.COMPLETE

        # Get result
        result = await mock_client.get_result(start_response.job_id)
        assert result.report is not None
