# File: test_server.py | Module: tests
"""Integration tests for server.py MCP server."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from server import (
    list_tools,
    call_tool,
    get_research_client,
    get_article_generator,
    get_image_generator,
    get_markdown_assembler,
)


class TestToolListing:
    """Tests for tool listing."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """Test all tools are listed."""
        tools = await list_tools()

        tool_names = [t.name for t in tools]
        assert "start_deep_research" in tool_names
        assert "check_research_status" in tool_names
        assert "get_research_result" in tool_names
        assert "generate_articles" in tool_names
        assert "generate_images" in tool_names
        assert "assemble_markdown" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_count(self):
        """Test correct number of tools."""
        tools = await list_tools()
        assert len(tools) == 6

    @pytest.mark.asyncio
    async def test_tool_schemas_valid(self):
        """Test all tools have valid input schemas."""
        tools = await list_tools()

        for tool in tools:
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"


class TestSingletonClients:
    """Tests for singleton client creation."""

    def test_get_research_client_singleton(self):
        """Test research client is singleton."""
        with patch("server._research_client", None):
            with patch("server.DeepResearchClient") as mock_class:
                mock_class.return_value = MagicMock()

                client1 = get_research_client()
                client2 = get_research_client()

                # Should only create one instance
                assert mock_class.call_count == 1

    def test_get_article_generator_singleton(self):
        """Test article generator is singleton."""
        with patch("server._article_generator", None):
            with patch("server.ArticleGenerator") as mock_class:
                mock_class.return_value = MagicMock()

                gen1 = get_article_generator()
                gen2 = get_article_generator()

                assert mock_class.call_count == 1

    def test_get_image_generator_singleton(self):
        """Test image generator is singleton."""
        with patch("server._image_generator", None):
            with patch("server.ImageGenerator") as mock_class:
                mock_class.return_value = MagicMock()

                gen1 = get_image_generator()
                gen2 = get_image_generator()

                assert mock_class.call_count == 1

    def test_get_markdown_assembler_singleton(self):
        """Test markdown assembler is singleton."""
        with patch("server._markdown_assembler", None):
            with patch("server.MarkdownAssembler") as mock_class:
                mock_class.return_value = MagicMock()

                asm1 = get_markdown_assembler()
                asm2 = get_markdown_assembler()

                assert mock_class.call_count == 1


class TestToolCalls:
    """Tests for tool call handling."""

    @pytest.fixture
    def mock_research_client(self):
        """Mock research client."""
        client = MagicMock()
        client.start = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"job_id": "test-123", "status": "started"}'
        ))
        client.check_status = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"status": "running", "progress": 50}'
        ))
        client.get_result = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"report": "Test report"}'
        ))
        return client

    @pytest.fixture
    def mock_article_generator(self):
        """Mock article generator."""
        gen = MagicMock()
        gen.generate_parallel = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"pro": "Pro article", "flash": "Flash article"}'
        ))
        return gen

    @pytest.fixture
    def mock_image_generator(self):
        """Mock image generator."""
        gen = MagicMock()
        gen.generate = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"paths": ["/path/to/image.png"]}'
        ))
        return gen

    @pytest.fixture
    def mock_markdown_assembler(self):
        """Mock markdown assembler."""
        asm = MagicMock()
        asm.assemble = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"markdown": "# Article"}'
        ))
        return asm

    @pytest.mark.asyncio
    async def test_call_start_deep_research(self, mock_research_client):
        """Test start_deep_research tool call."""
        with patch("server.get_research_client", return_value=mock_research_client):
            result = await call_tool("start_deep_research", {
                "spec": {"research_goal": "Test research"}
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["job_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_call_check_research_status(self, mock_research_client):
        """Test check_research_status tool call."""
        with patch("server.get_research_client", return_value=mock_research_client):
            result = await call_tool("check_research_status", {
                "job_id": "test-123"
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_call_get_research_result(self, mock_research_client):
        """Test get_research_result tool call."""
        with patch("server.get_research_client", return_value=mock_research_client):
            result = await call_tool("get_research_result", {
                "job_id": "test-123"
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert "report" in data

    @pytest.mark.asyncio
    async def test_call_generate_articles(self, mock_article_generator):
        """Test generate_articles tool call."""
        with patch("server.get_article_generator", return_value=mock_article_generator):
            result = await call_tool("generate_articles", {
                "research": "Test research content",
                "spec": {"research_goal": "Test"}
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert "pro" in data
            assert "flash" in data

    @pytest.mark.asyncio
    async def test_call_generate_images(self, mock_image_generator):
        """Test generate_images tool call."""
        with patch("server.get_image_generator", return_value=mock_image_generator):
            result = await call_tool("generate_images", {
                "prompts": [{"description": "Test image"}],
                "output_dir": "/tmp/test"
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert "paths" in data

    @pytest.mark.asyncio
    async def test_call_assemble_markdown(self, mock_markdown_assembler):
        """Test assemble_markdown tool call."""
        with patch("server.get_markdown_assembler", return_value=mock_markdown_assembler):
            result = await call_tool("assemble_markdown", {
                "draft": "# Article\n\nContent",
                "images": ["/path/to/image.png"],
                "format": "blog"
            })

            assert len(result) == 1
            data = json.loads(result[0].text)
            assert "markdown" in data

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test unknown tool returns error."""
        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data
        assert "Unknown tool" in data["error"]

    @pytest.mark.asyncio
    async def test_call_tool_error_handling(self, mock_research_client):
        """Test error handling in tool calls."""
        mock_research_client.start = AsyncMock(side_effect=Exception("Test error"))

        with patch("server.get_research_client", return_value=mock_research_client):
            result = await call_tool("start_deep_research", {
                "spec": {"research_goal": "Test"}
            })

            data = json.loads(result[0].text)
            assert "error" in data
            assert data["recoverable"] is True


class TestServerIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_research_flow_mocked(self):
        """Test full research flow with mocked clients."""
        # Create mocks
        mock_client = MagicMock()
        mock_client.start = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"job_id": "test-job", "status": "started"}'
        ))
        mock_client.check_status = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"status": "complete", "progress": 100}'
        ))
        mock_client.get_result = AsyncMock(return_value=MagicMock(
            model_dump_json=lambda: '{"report": "Research findings", "sources": []}'
        ))

        with patch("server.get_research_client", return_value=mock_client):
            # Start research
            start_result = await call_tool("start_deep_research", {
                "spec": {"research_goal": "Test topic"}
            })
            start_data = json.loads(start_result[0].text)
            assert start_data["status"] == "started"

            # Check status
            status_result = await call_tool("check_research_status", {
                "job_id": start_data["job_id"]
            })
            status_data = json.loads(status_result[0].text)
            assert status_data["status"] == "complete"

            # Get result
            result = await call_tool("get_research_result", {
                "job_id": start_data["job_id"]
            })
            result_data = json.loads(result[0].text)
            assert "report" in result_data
