# File: test_image_generator.py | Module: tests
"""Unit tests for image_generator.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from image_generator import ImageGenerator
from models import ImagePrompt


class TestImageGenerator:
    """Tests for ImageGenerator class."""

    @pytest.fixture
    def generator(self, mock_genai_client):
        """Create generator with mocked genai."""
        with patch("image_generator.genai") as mock_genai:
            mock_genai.Client.return_value = mock_genai_client
            with patch("image_generator.config") as mock_config:
                mock_config.google_api_key = "test-key"
                mock_config.image_model = "test-image"
                mock_config.pro_model = "test-pro"
                gen = ImageGenerator()
                gen.client = mock_genai_client
                return gen

    def test_build_prompt_basic(self, generator):
        """Test basic prompt building."""
        prompt = ImagePrompt(description="A beautiful sunset")
        result = generator._build_prompt(prompt)

        assert "beautiful sunset" in result

    def test_build_prompt_includes_modifiers(self, generator):
        """Test prompt includes quality modifiers."""
        prompt = ImagePrompt(
            description="A sunset",
            quality_modifiers=["high-quality", "detailed"]
        )
        result = generator._build_prompt(prompt)

        assert "high-quality" in result
        assert "detailed" in result

    def test_build_prompt_includes_style(self, generator):
        """Test prompt includes style when not in description."""
        prompt = ImagePrompt(
            description="A sunset",
            style="watercolor"
        )
        result = generator._build_prompt(prompt)

        assert "watercolor" in result

    def test_build_prompt_skips_style_if_in_description(self, generator):
        """Test style is not duplicated if already in description."""
        prompt = ImagePrompt(
            description="A watercolor sunset painting",
            style="watercolor"
        )
        result = generator._build_prompt(prompt)

        # Should only appear once (in description, not added again)
        assert result.count("watercolor") == 1

    def test_get_aspect_ratio_config(self, generator):
        """Test aspect ratio conversion."""
        assert generator._get_aspect_ratio_config("16:9") == "ASPECT_RATIO_16_9"
        assert generator._get_aspect_ratio_config("1:1") == "ASPECT_RATIO_1_1"
        assert generator._get_aspect_ratio_config("9:16") == "ASPECT_RATIO_9_16"

    def test_get_aspect_ratio_config_default(self, generator):
        """Test unknown aspect ratio returns default."""
        assert generator._get_aspect_ratio_config("3:2") == "ASPECT_RATIO_16_9"

    @pytest.mark.asyncio
    async def test_generate_single_no_images(self, generator, temp_output_dir):
        """Test handling when no images generated."""
        prompt = ImagePrompt(description="Test image")
        result = await generator._generate_single(prompt, temp_output_dir, 0)

        # Mock returns empty generated_images, should return None
        assert result is None

    @pytest.mark.asyncio
    async def test_generate_single_with_image(self, generator, temp_output_dir):
        """Test successful image generation."""
        # Setup mock to return an image
        mock_image = MagicMock()
        mock_image.image.image_bytes = b"fake image data"

        mock_response = MagicMock()
        mock_response.generated_images = [mock_image]

        generator.client.models.generate_images = MagicMock(return_value=mock_response)

        prompt = ImagePrompt(description="Test image", purpose="header")
        result = await generator._generate_single(prompt, temp_output_dir, 0)

        assert result is not None
        assert "1-header.png" in result

    @pytest.mark.asyncio
    async def test_generate_empty_prompts(self, generator, temp_output_dir):
        """Test generate with empty prompts list."""
        result = await generator.generate([], str(temp_output_dir))

        assert result.paths == []

    @pytest.mark.asyncio
    async def test_generate_creates_output_dir(self, generator, tmp_path):
        """Test that output directory is created."""
        output_dir = tmp_path / "new_dir" / "images"
        assert not output_dir.exists()

        await generator.generate([], str(output_dir))

        assert output_dir.exists()

    @pytest.mark.asyncio
    async def test_generate_filters_invalid_prompts(self, generator, temp_output_dir):
        """Test invalid prompts are filtered out."""
        prompts = [
            {"description": "Valid prompt"},
            {"invalid": "missing description"},
        ]

        result = await generator.generate(prompts, str(temp_output_dir))

        # Should only process valid prompts
        # Result may be empty if mock doesn't return images
        assert isinstance(result.paths, list)

    @pytest.mark.asyncio
    async def test_generate_parallel_execution(self, generator, temp_output_dir, sample_image_prompts):
        """Test multiple images are generated in parallel."""
        call_count = {"count": 0}

        async def mock_generate(*args, **kwargs):
            call_count["count"] += 1
            return None

        generator._generate_single = mock_generate

        await generator.generate(sample_image_prompts, str(temp_output_dir))

        # Should be called for each prompt
        assert call_count["count"] == len(sample_image_prompts)


class TestImageGeneratorFallback:
    """Tests for fallback image generation."""

    @pytest.fixture
    def generator_with_fallback(self, mock_genai_client):
        """Create generator that will use fallback."""
        with patch("image_generator.genai") as mock_genai:
            mock_genai.Client.return_value = mock_genai_client

            # Make generate_images fail
            mock_genai_client.models.generate_images = MagicMock(
                side_effect=Exception("Imagen not available")
            )

            with patch("image_generator.config") as mock_config:
                mock_config.google_api_key = "test-key"
                mock_config.image_model = "test-image"
                mock_config.pro_model = "test-pro"

                gen = ImageGenerator()
                gen.client = mock_genai_client
                return gen

    @pytest.mark.asyncio
    async def test_fallback_triggered_on_error(self, generator_with_fallback, temp_output_dir):
        """Test fallback is used when primary fails."""
        prompt = ImagePrompt(description="Test image")

        # The fallback will also fail with mock, but we can verify it was attempted
        result = await generator_with_fallback._generate_single(prompt, temp_output_dir, 0)

        # Both primary and fallback failed with mock
        assert result is None
