# File: test_article_generator.py | Module: tests
"""Unit tests for article_generator.py."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from article_generator import ArticleGenerator
from models import ResearchSpec


class TestArticleGenerator:
    """Tests for ArticleGenerator class."""

    @pytest.fixture
    def generator(self, mock_genai_client):
        """Create generator with mocked genai."""
        with patch("article_generator.genai") as mock_genai:
            mock_genai.Client.return_value = mock_genai_client
            with patch("article_generator.config") as mock_config:
                mock_config.google_api_key = "test-key"
                mock_config.pro_model = "test-pro"
                mock_config.flash_model = "test-flash"
                gen = ArticleGenerator()
                gen.client = mock_genai_client
                return gen

    def test_build_prompt_includes_research(self, generator, sample_research_spec):
        """Test prompt includes research content."""
        spec = ResearchSpec(**sample_research_spec)
        prompt = generator._build_prompt("Research content here", spec)

        assert "Research content here" in prompt

    def test_build_prompt_includes_audience(self, generator, sample_research_spec):
        """Test prompt includes audience level."""
        spec = ResearchSpec(**sample_research_spec)
        prompt = generator._build_prompt("Research", spec)

        assert "intermediate" in prompt.lower()

    def test_build_prompt_includes_format(self, generator, sample_research_spec):
        """Test prompt includes format."""
        spec = ResearchSpec(**sample_research_spec)
        prompt = generator._build_prompt("Research", spec)

        assert "blog" in prompt.lower()

    def test_build_prompt_includes_word_count(self, generator, sample_research_spec):
        """Test prompt includes word count."""
        spec = ResearchSpec(**sample_research_spec)
        prompt = generator._build_prompt("Research", spec)

        assert "2000" in prompt

    @pytest.mark.asyncio
    async def test_generate_with_model(self, generator):
        """Test generating with a specific model."""
        result = await generator._generate_with_model("test-model", "Test prompt")
        assert result == "Sample generated content"

    @pytest.mark.asyncio
    async def test_generate_with_model_error(self, generator):
        """Test error handling in generate_with_model."""
        generator.client.models.generate_content = MagicMock(
            side_effect=Exception("API Error")
        )
        result = await generator._generate_with_model("test-model", "Test prompt")
        assert "Error generating" in result

    @pytest.mark.asyncio
    async def test_generate_parallel_returns_both(self, generator, sample_research_spec):
        """Test parallel generation returns both articles."""
        result = await generator.generate_parallel("Research content", sample_research_spec)

        assert result.pro is not None
        assert result.flash is not None

    @pytest.mark.asyncio
    async def test_generate_parallel_invalid_spec(self, generator):
        """Test invalid spec raises error."""
        with pytest.raises(ValueError, match="Invalid spec"):
            await generator.generate_parallel("Research", {})

    @pytest.mark.asyncio
    async def test_generate_parallel_calls_both_models(self, generator, sample_research_spec):
        """Test both pro and flash models are called."""
        call_count = {"count": 0}

        def mock_generate(*args, **kwargs):
            call_count["count"] += 1
            response = MagicMock()
            response.text = f"Article {call_count['count']}"
            return response

        generator.client.models.generate_content = mock_generate

        await generator.generate_parallel("Research content", sample_research_spec)

        # Should be called twice (once for pro, once for flash)
        assert call_count["count"] == 2
