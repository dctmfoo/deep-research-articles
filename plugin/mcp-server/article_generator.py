# File: article_generator.py | Module: mcp-server
"""Article generation using Gemini Pro and Flash models in parallel."""

from __future__ import annotations

import asyncio
from typing import Any

from google import genai
from google.genai import types

from config import config
from logger import logger
from models import ArticleGenerationResult, ResearchSpec


class ArticleGenerator:
    """Generates articles using Gemini Pro and Flash in parallel."""

    def __init__(self) -> None:
        """Initialize the article generator."""
        self.client = genai.Client(api_key=config.google_api_key)

    def _build_prompt(self, research: str, spec: ResearchSpec) -> str:
        """Build the article generation prompt."""
        audience = spec.audience.expertise_level or "general"
        format_type = spec.output_preferences.format or "blog"
        word_count = spec.output_preferences.word_count or 2000
        
        return f"""Based on the following research, write a comprehensive article.

## Research
{research}

## Requirements
- Target audience: {audience} level readers
- Format: {format_type} post
- Target word count: ~{word_count} words
- Tone: Professional but accessible
- Include specific examples and data points
- Structure with clear sections and headings
- Include citations to sources where appropriate

Write the article in markdown format with proper headings, paragraphs, and formatting."""

    async def _generate_with_model(self, model: str, prompt: str) -> str:
        """Generate article content with a specific model."""
        import time
        logger.api_call("gemini", "generate_content", model=model, prompt_len=len(prompt))
        start_time = time.time()
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=8192,
                ),
            )
            duration_ms = (time.time() - start_time) * 1000
            result = response.text if response.text else ""
            logger.api_response("gemini", "generate_content", duration_ms, success=True)
            logger.debug(f"Model {model} generated {len(result)} chars")
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.api_response("gemini", "generate_content", duration_ms, success=False)
            logger.error(f"Article generation failed with {model}: {e}")
            return f"Error generating with {model}: {str(e)}"

    async def generate_parallel(
        self, research: str, spec: dict[str, Any]
    ) -> ArticleGenerationResult:
        """Generate articles with both Pro and Flash models in parallel."""
        logger.phase_start("Article Generation", "parallel Pro + Flash")
        try:
            research_spec = ResearchSpec(**spec)
        except Exception as e:
            logger.error(f"Invalid spec: {e}")
            raise ValueError(f"Invalid spec: {e}")

        prompt = self._build_prompt(research, research_spec)
        logger.debug(f"Built prompt with {len(prompt)} chars")

        # Run both models in parallel
        logger.info("Starting parallel generation with Pro and Flash models")
        pro_task = asyncio.create_task(
            self._generate_with_model(config.pro_model, prompt)
        )
        flash_task = asyncio.create_task(
            self._generate_with_model(config.flash_model, prompt)
        )

        pro_result, flash_result = await asyncio.gather(pro_task, flash_task)

        logger.phase_end("Article Generation", success=True,
                        details=f"pro={len(pro_result)} chars, flash={len(flash_result)} chars")
        return ArticleGenerationResult(
            pro=pro_result,
            flash=flash_result,
        )
