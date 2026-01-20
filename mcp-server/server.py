# File: server.py | Module: mcp-server
"""MCP server entry point for Deep Research Articles plugin."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our modules
from article_generator import ArticleGenerator
from deep_research import DeepResearchClient
from image_generator import ImageGenerator
from logger import logger
from markdown_assembler import MarkdownAssembler


# Create server instance
server = Server("gemini-research")

# Create singleton clients
_research_client: DeepResearchClient | None = None
_article_generator: ArticleGenerator | None = None
_image_generator: ImageGenerator | None = None
_markdown_assembler: MarkdownAssembler | None = None


def get_research_client() -> DeepResearchClient:
    """Get or create the research client."""
    global _research_client
    if _research_client is None:
        _research_client = DeepResearchClient()
    return _research_client


def get_article_generator() -> ArticleGenerator:
    """Get or create the article generator."""
    global _article_generator
    if _article_generator is None:
        _article_generator = ArticleGenerator()
    return _article_generator


def get_image_generator() -> ImageGenerator:
    """Get or create the image generator."""
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


def get_markdown_assembler() -> MarkdownAssembler:
    """Get or create the markdown assembler."""
    global _markdown_assembler
    if _markdown_assembler is None:
        _markdown_assembler = MarkdownAssembler()
    return _markdown_assembler


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="start_deep_research",
            description="Start an async deep research job on a topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "spec": {
                        "type": "object",
                        "description": "Research specification from clarification phase",
                    }
                },
                "required": ["spec"],
            },
        ),
        Tool(
            name="check_research_status",
            description="Check the status of a running research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID from start_deep_research",
                    }
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="get_research_result",
            description="Get the result of a completed research job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {"type": "string"}
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="generate_articles",
            description="Generate articles using Gemini Pro and Flash in parallel",
            inputSchema={
                "type": "object",
                "properties": {
                    "research": {
                        "type": "string",
                        "description": "Research report content",
                    },
                    "spec": {
                        "type": "object",
                        "description": "Research specification",
                    },
                },
                "required": ["research", "spec"],
            },
        ),
        Tool(
            name="generate_images",
            description="Generate images from prompts using Gemini Pro Image",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompts": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Array of image prompts",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to save images",
                    },
                },
                "required": ["prompts", "output_dir"],
            },
        ),
        Tool(
            name="assemble_markdown",
            description="Create final markdown with embedded images",
            inputSchema={
                "type": "object",
                "properties": {
                    "draft": {
                        "type": "string",
                        "description": "Article draft content",
                    },
                    "images": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Image file paths",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["blog", "x_article", "linkedin"],
                        "description": "Target platform format",
                    },
                },
                "required": ["draft", "images"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"[MCP] Tool called: {name}")
    logger.debug(f"[MCP] Arguments: {list(arguments.keys())}")
    try:
        if name == "start_deep_research":
            client = get_research_client()
            result = await client.start(arguments["spec"])
            return [TextContent(type="text", text=result.model_dump_json())]

        elif name == "check_research_status":
            client = get_research_client()
            result = await client.check_status(arguments["job_id"])
            return [TextContent(type="text", text=result.model_dump_json())]

        elif name == "get_research_result":
            client = get_research_client()
            result = await client.get_result(arguments["job_id"])
            return [TextContent(type="text", text=result.model_dump_json())]

        elif name == "generate_articles":
            generator = get_article_generator()
            result = await generator.generate_parallel(
                arguments["research"], arguments["spec"]
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        elif name == "generate_images":
            generator = get_image_generator()
            result = await generator.generate(
                arguments["prompts"], arguments["output_dir"]
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        elif name == "assemble_markdown":
            assembler = get_markdown_assembler()
            result = await assembler.assemble(
                arguments["draft"],
                arguments["images"],
                arguments.get("format", "blog"),
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        else:
            logger.warning(f"[MCP] Unknown tool: {name}")
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    except Exception as e:
        logger.error(f"[MCP] Tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e), "recoverable": True}))]


async def main() -> None:
    """Run the MCP server."""
    logger.info("Deep Research Articles MCP server starting...")
    logger.info(f"Debug mode: {logger.is_debug}")
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server ready, accepting connections")
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
