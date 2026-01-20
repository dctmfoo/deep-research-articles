# File: image_generator.py | Module: mcp-server
"""Image generation using Imagen 3."""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from config import config
from logger import logger
from models import ImageGenerationResult, ImagePrompt


class ImageGenerator:
    """Generates images using Imagen 3."""

    def __init__(self) -> None:
        """Initialize the image generator."""
        self.client = genai.Client(api_key=config.google_api_key)

    def _build_prompt(self, prompt: ImagePrompt) -> str:
        """Build the full prompt including modifiers."""
        parts = [prompt.description]

        if prompt.quality_modifiers:
            parts.append(", ".join(prompt.quality_modifiers))

        if prompt.style and prompt.style.lower() not in prompt.description.lower():
            parts.append(f"Style: {prompt.style}")

        return ". ".join(parts)

    def _get_aspect_ratio_config(self, aspect_ratio: str) -> str:
        """Convert aspect ratio string to Imagen config."""
        ratio_map = {
            "16:9": "ASPECT_RATIO_16_9",
            "9:16": "ASPECT_RATIO_9_16",
            "1:1": "ASPECT_RATIO_1_1",
            "4:3": "ASPECT_RATIO_4_3",
            "3:4": "ASPECT_RATIO_3_4",
        }
        return ratio_map.get(aspect_ratio, "ASPECT_RATIO_16_9")

    async def _generate_single(
        self, prompt: ImagePrompt, output_path: Path, index: int
    ) -> str | None:
        """Generate a single image using Imagen."""
        full_prompt = self._build_prompt(prompt)
        logger.api_call("imagen", "generate_images", model=config.image_model, purpose=prompt.purpose)

        try:
            import time
            start_time = time.time()
            # Use Imagen for image generation
            response = await asyncio.to_thread(
                self.client.models.generate_images,
                model=config.image_model,
                prompt=full_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=self._get_aspect_ratio_config(prompt.aspect_ratio),
                    safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                    person_generation="ALLOW_ADULT",
                ),
            )

            duration_ms = (time.time() - start_time) * 1000

            # Save the generated image
            if response.generated_images:
                image = response.generated_images[0]
                filename = f"{index + 1}-{prompt.purpose}.png"
                filepath = output_path / filename

                # Image data is in base64
                if hasattr(image, 'image') and image.image:
                    if hasattr(image.image, 'image_bytes'):
                        filepath.write_bytes(image.image.image_bytes)
                    elif hasattr(image.image, 'data'):
                        image_data = base64.b64decode(image.image.data)
                        filepath.write_bytes(image_data)
                    logger.api_response("imagen", "generate_images", duration_ms, success=True)
                    logger.debug(f"Saved image to {filepath}")
                    return str(filepath)

            logger.warning(f"No image generated for prompt {index + 1}")
            return None

        except Exception as e:
            logger.warning(f"Imagen failed for image {index + 1}: {e}, trying fallback")
            # Try fallback with gemini model for image generation
            return await self._generate_fallback(prompt, output_path, index)

    async def _generate_fallback(
        self, prompt: ImagePrompt, output_path: Path, index: int
    ) -> str | None:
        """Fallback image generation using Gemini image model with image output."""
        full_prompt = self._build_prompt(prompt)
        logger.api_call("gemini", "generate_content", model=config.image_model, fallback=True)

        try:
            import time
            start_time = time.time()
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=config.image_model,
                contents=f"Generate an image: {full_prompt}",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            duration_ms = (time.time() - start_time) * 1000

            # Extract image from response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        filename = f"{index + 1}-{prompt.purpose}.png"
                        filepath = output_path / filename

                        if hasattr(part.inline_data, 'data'):
                            image_data = base64.b64decode(part.inline_data.data)
                            filepath.write_bytes(image_data)
                            logger.api_response("gemini", "generate_content", duration_ms, success=True)
                            logger.debug(f"Fallback saved image to {filepath}")
                            return str(filepath)

            logger.warning(f"Fallback produced no image for prompt {index + 1}")
            return None

        except Exception as e:
            logger.error(f"Fallback image generation failed: {e}")
            return None

    async def generate(
        self, prompts: list[dict[str, Any]], output_dir: str
    ) -> ImageGenerationResult:
        """Generate images from prompts."""
        logger.phase_start("Image Generation", f"{len(prompts)} prompts")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory: {output_path}")

        # Parse prompts
        image_prompts = []
        for p in prompts:
            try:
                image_prompts.append(ImagePrompt(**p))
            except Exception as e:
                logger.warning(f"Invalid prompt skipped: {e}")
                continue

        logger.info(f"Generating {len(image_prompts)} images in parallel")

        # Generate images in parallel
        tasks = [
            self._generate_single(prompt, output_path, i)
            for i, prompt in enumerate(image_prompts)
        ]

        results = await asyncio.gather(*tasks)

        # Filter out None results
        paths = [p for p in results if p is not None]

        logger.phase_end("Image Generation", success=True, details=f"{len(paths)}/{len(image_prompts)} images created")
        return ImageGenerationResult(paths=paths)
