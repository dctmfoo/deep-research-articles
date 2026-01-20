# File: markdown_assembler.py | Module: mcp-server
"""Markdown assembly with embedded images."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from google import genai
from google.genai import types

from config import config
from logger import logger
from models import MarkdownAssemblyResult, MarkdownMetadata


class MarkdownAssembler:
    """Assembles final markdown with images."""

    def __init__(self) -> None:
        """Initialize the assembler."""
        self.client = genai.Client(api_key=config.google_api_key)

    def _count_words(self, text: str) -> int:
        """Count words in text."""
        return len(text.split())

    def _extract_title(self, markdown: str) -> str:
        """Extract title from markdown."""
        lines = markdown.strip().split("\n")
        for line in lines:
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled Article"

    def _extract_description(self, markdown: str) -> str:
        """Extract description from first paragraph."""
        lines = markdown.strip().split("\n")
        in_content = False
        
        for line in lines:
            if line.startswith("# "):
                in_content = True
                continue
            if in_content and line.strip() and not line.startswith("#"):
                # Return first 160 characters of first paragraph
                return line.strip()[:160]
        
        return ""

    async def assemble(
        self, draft: str, images: list[str], format: str = "blog"
    ) -> MarkdownAssemblyResult:
        """Assemble final markdown with images."""
        logger.phase_start("Markdown Assembly", f"format={format}, images={len(images)}")
        logger.debug(f"Draft length: {len(draft)} chars")

        # Use Gemini to intelligently place images
        prompt = f"""You are a markdown editor. Given an article and a list of image paths, insert the images at appropriate locations in the article.

## Article
{draft}

## Available Images
{chr(10).join(f'- {img}' for img in images)}

## Instructions
1. Insert the first image as a header image after the title
2. Place other images near relevant sections
3. Add appropriate alt text based on the image filename
4. Use markdown image syntax: ![Alt text](path)
5. Return the complete article with images inserted

Return ONLY the markdown, no explanations."""

        try:
            import time
            logger.api_call("gemini", "generate_content", model=config.pro_model, task="image_placement")
            start_time = time.time()
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=config.pro_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=8192,
                ),
            )
            duration_ms = (time.time() - start_time) * 1000
            logger.api_response("gemini", "generate_content", duration_ms, success=True)

            assembled = response.text if response.text else draft
            logger.debug(f"Assembled markdown: {len(assembled)} chars")

        except Exception as e:
            logger.warning(f"Gemini assembly failed: {e}, using fallback")
            # Fallback: simple image insertion
            lines = draft.split("\n")
            
            # Insert header image after title
            if images and lines:
                for i, line in enumerate(lines):
                    if line.startswith("# "):
                        header_img = f"\n![Header Image]({images[0]})\n"
                        lines.insert(i + 1, header_img)
                        break
            
            assembled = "\n".join(lines)

        # Extract metadata
        title = self._extract_title(assembled)
        description = self._extract_description(assembled)
        word_count = self._count_words(assembled)
        
        # Extract tags from content (simple approach)
        tags = []

        logger.phase_end("Markdown Assembly", success=True,
                        details=f"title={title[:30]}, words={word_count}")
        return MarkdownAssemblyResult(
            markdown=assembled,
            metadata=MarkdownMetadata(
                title=title,
                description=description,
                word_count=word_count,
                tags=tags,
            ),
        )
