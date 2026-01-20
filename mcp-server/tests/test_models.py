# File: test_models.py | Module: tests
"""Unit tests for models.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models import (
    ResearchSpec,
    ResearchStatus,
    ResearchStartResponse,
    ResearchStatusResponse,
    ResearchResult,
    ResearchResultSource,
    ResearchResultMetadata,
    ArticleGenerationResult,
    ImagePrompt,
    ImageGenerationResult,
    MarkdownAssemblyResult,
    MarkdownMetadata,
    Scope,
    Audience,
    OutputPreferences,
    Constraints,
)


class TestResearchSpec:
    """Tests for ResearchSpec model."""

    def test_minimal_spec(self):
        """Test creating spec with only required field."""
        spec = ResearchSpec(research_goal="Test goal")
        assert spec.research_goal == "Test goal"
        assert spec.domain == ""
        assert spec.scope.breadth == "moderate"
        assert spec.scope.depth == "detailed"

    def test_full_spec(self, sample_research_spec):
        """Test creating spec with all fields."""
        spec = ResearchSpec(**sample_research_spec)
        assert spec.research_goal == "Understanding quantum computing basics"
        assert spec.domain == "technology"
        assert spec.focus_areas == ["qubits", "quantum gates", "practical applications"]
        assert spec.audience.expertise_level == "intermediate"

    def test_spec_missing_required_field(self):
        """Test that missing research_goal raises error."""
        with pytest.raises(ValidationError):
            ResearchSpec()


class TestResearchStatus:
    """Tests for ResearchStatus enum."""

    def test_status_values(self):
        """Test enum values."""
        assert ResearchStatus.RUNNING == "running"
        assert ResearchStatus.COMPLETE == "complete"
        assert ResearchStatus.FAILED == "failed"


class TestResearchStartResponse:
    """Tests for ResearchStartResponse model."""

    def test_start_response(self):
        """Test creating start response."""
        response = ResearchStartResponse(job_id="test-123")
        assert response.job_id == "test-123"
        assert response.status == "started"
        assert response.estimated_time_seconds == 600

    def test_start_response_custom_estimate(self):
        """Test custom estimated time."""
        response = ResearchStartResponse(
            job_id="test-123",
            estimated_time_seconds=1800
        )
        assert response.estimated_time_seconds == 1800


class TestResearchStatusResponse:
    """Tests for ResearchStatusResponse model."""

    def test_status_response_running(self):
        """Test running status response."""
        response = ResearchStatusResponse(
            status=ResearchStatus.RUNNING,
            progress=50,
            message="Researching..."
        )
        assert response.status == ResearchStatus.RUNNING
        assert response.progress == 50

    def test_progress_bounds(self):
        """Test progress is bounded 0-100."""
        with pytest.raises(ValidationError):
            ResearchStatusResponse(
                status=ResearchStatus.RUNNING,
                progress=150
            )

        with pytest.raises(ValidationError):
            ResearchStatusResponse(
                status=ResearchStatus.RUNNING,
                progress=-10
            )


class TestResearchResult:
    """Tests for ResearchResult model."""

    def test_result_with_sources(self):
        """Test result with sources."""
        sources = [
            ResearchResultSource(title="Source 1", url="https://example.com/1"),
            ResearchResultSource(title="Source 2", url="https://example.com/2"),
        ]
        result = ResearchResult(
            report="# Research Report\n\nContent here.",
            sources=sources,
            metadata=ResearchResultMetadata(
                duration_seconds=120.5,
                sources_analyzed=10,
            ),
        )
        assert len(result.sources) == 2
        assert result.metadata.duration_seconds == 120.5


class TestImagePrompt:
    """Tests for ImagePrompt model."""

    def test_image_prompt_defaults(self):
        """Test default values."""
        prompt = ImagePrompt(description="A beautiful sunset")
        assert prompt.style == "photorealistic"
        assert prompt.aspect_ratio == "16:9"
        assert prompt.purpose == "visual"
        assert "high-quality" in prompt.quality_modifiers

    def test_image_prompt_custom(self):
        """Test custom values."""
        prompt = ImagePrompt(
            description="Technical diagram",
            style="illustration",
            aspect_ratio="1:1",
            purpose="diagram",
            quality_modifiers=["clean", "simple"],
        )
        assert prompt.style == "illustration"
        assert prompt.aspect_ratio == "1:1"


class TestArticleGenerationResult:
    """Tests for ArticleGenerationResult model."""

    def test_article_result(self):
        """Test article generation result."""
        result = ArticleGenerationResult(
            pro="# Pro Article\n\nDetailed content.",
            flash="# Flash Article\n\nConcise content.",
        )
        assert "Pro Article" in result.pro
        assert "Flash Article" in result.flash


class TestMarkdownAssemblyResult:
    """Tests for MarkdownAssemblyResult model."""

    def test_assembly_result(self):
        """Test markdown assembly result."""
        result = MarkdownAssemblyResult(
            markdown="# Final Article\n\n![Image](image.png)",
            metadata=MarkdownMetadata(
                title="Final Article",
                description="A great article",
                word_count=1500,
                tags=["tech", "ai"],
            ),
        )
        assert "Final Article" in result.markdown
        assert result.metadata.word_count == 1500
        assert "tech" in result.metadata.tags
