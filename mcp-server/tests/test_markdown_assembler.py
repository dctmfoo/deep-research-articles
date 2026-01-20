# File: test_markdown_assembler.py | Module: tests
"""Unit tests for markdown_assembler.py."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from markdown_assembler import MarkdownAssembler


class TestMarkdownAssembler:
    """Tests for MarkdownAssembler class."""

    @pytest.fixture
    def assembler(self, mock_genai_client):
        """Create assembler with mocked genai."""
        with patch("markdown_assembler.genai") as mock_genai:
            mock_genai.Client.return_value = mock_genai_client
            with patch("markdown_assembler.config") as mock_config:
                mock_config.google_api_key = "test-key"
                mock_config.pro_model = "test-pro"
                asm = MarkdownAssembler()
                asm.client = mock_genai_client
                return asm

    def test_count_words(self, assembler):
        """Test word counting."""
        assert assembler._count_words("one two three") == 3
        assert assembler._count_words("hello") == 1
        assert assembler._count_words("") == 0  # split() on empty returns []
        assert assembler._count_words("a b c d e f g h i j") == 10

    def test_extract_title_with_h1(self, assembler):
        """Test title extraction from H1."""
        markdown = "# My Great Article\n\nContent here."
        title = assembler._extract_title(markdown)
        assert title == "My Great Article"

    def test_extract_title_no_h1(self, assembler):
        """Test title extraction when no H1."""
        markdown = "## Subheading\n\nContent here."
        title = assembler._extract_title(markdown)
        assert title == "Untitled Article"

    def test_extract_title_multiple_h1(self, assembler):
        """Test only first H1 is used."""
        markdown = "# First Title\n\n# Second Title\n\nContent."
        title = assembler._extract_title(markdown)
        assert title == "First Title"

    def test_extract_description_from_first_paragraph(self, assembler):
        """Test description extraction."""
        markdown = "# Title\n\nThis is the first paragraph of content.\n\n## Section"
        desc = assembler._extract_description(markdown)
        assert "first paragraph" in desc

    def test_extract_description_truncates(self, assembler):
        """Test description is truncated to 160 chars."""
        long_paragraph = "a" * 200
        markdown = f"# Title\n\n{long_paragraph}"
        desc = assembler._extract_description(markdown)
        assert len(desc) <= 160

    def test_extract_description_skips_headings(self, assembler):
        """Test headings are not used as description."""
        markdown = "# Title\n\n## Subheading\n\nActual content here."
        desc = assembler._extract_description(markdown)
        assert "Actual content" in desc

    @pytest.mark.asyncio
    async def test_assemble_with_images(self, assembler):
        """Test assembly with images."""
        draft = "# Article\n\nContent here."
        images = ["/path/to/image1.png", "/path/to/image2.png"]

        # Mock response includes images
        mock_response = MagicMock()
        mock_response.text = "# Article\n\n![Image](image1.png)\n\nContent here."
        assembler.client.models.generate_content = MagicMock(return_value=mock_response)

        result = await assembler.assemble(draft, images, "blog")

        assert result.markdown is not None
        assert result.metadata.title == "Article"

    @pytest.mark.asyncio
    async def test_assemble_fallback_on_error(self, assembler):
        """Test fallback when API fails."""
        draft = "# Test Article\n\nContent here."
        images = ["/path/to/header.png"]

        # Make API fail
        assembler.client.models.generate_content = MagicMock(
            side_effect=Exception("API Error")
        )

        result = await assembler.assemble(draft, images, "blog")

        # Should use fallback
        assert "Test Article" in result.markdown
        assert "header.png" in result.markdown

    @pytest.mark.asyncio
    async def test_assemble_empty_images(self, assembler):
        """Test assembly with no images."""
        draft = "# Article\n\nContent here."
        images = []

        mock_response = MagicMock()
        mock_response.text = draft
        assembler.client.models.generate_content = MagicMock(return_value=mock_response)

        result = await assembler.assemble(draft, images, "blog")

        assert result.markdown == draft

    @pytest.mark.asyncio
    async def test_assemble_metadata_populated(self, assembler):
        """Test metadata is correctly populated."""
        draft = "# Test Title\n\nFirst paragraph description.\n\nMore content."
        images = []

        mock_response = MagicMock()
        mock_response.text = draft
        assembler.client.models.generate_content = MagicMock(return_value=mock_response)

        result = await assembler.assemble(draft, images, "blog")

        assert result.metadata.title == "Test Title"
        assert "First paragraph" in result.metadata.description
        assert result.metadata.word_count > 0

    @pytest.mark.asyncio
    async def test_assemble_different_formats(self, assembler):
        """Test assembly with different formats."""
        draft = "# Article\n\nContent."
        images = []

        mock_response = MagicMock()
        mock_response.text = draft
        assembler.client.models.generate_content = MagicMock(return_value=mock_response)

        for format_type in ["blog", "x_article", "linkedin"]:
            result = await assembler.assemble(draft, images, format_type)
            assert result is not None
