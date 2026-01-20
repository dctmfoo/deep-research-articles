# File: conftest.py | Module: tests
"""Shared pytest fixtures for Deep Research Articles tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, AsyncMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_research_spec() -> dict[str, Any]:
    """Sample research specification for testing."""
    return {
        "research_goal": "Understanding quantum computing basics",
        "domain": "technology",
        "scope": {
            "breadth": "moderate",
            "depth": "detailed",
        },
        "audience": {
            "expertise_level": "intermediate",
            "context": "Tech professionals wanting to understand quantum",
        },
        "focus_areas": ["qubits", "quantum gates", "practical applications"],
        "exclusions": ["quantum physics theory"],
        "constraints": {
            "recency": "recent",
            "geographic": "",
        },
        "output_preferences": {
            "format": "blog",
            "word_count": 2000,
            "include_sources": True,
            "include_images": True,
        },
        "clarification_notes": "",
    }


@pytest.fixture
def sample_image_prompts() -> list[dict[str, Any]]:
    """Sample image prompts for testing."""
    return [
        {
            "description": "A photorealistic quantum computer with glowing qubits",
            "style": "photorealistic",
            "quality_modifiers": ["high-quality", "detailed"],
            "aspect_ratio": "16:9",
            "purpose": "header",
        },
        {
            "description": "Diagram showing quantum gate operations",
            "style": "technical illustration",
            "quality_modifiers": ["clean", "educational"],
            "aspect_ratio": "16:9",
            "purpose": "diagram",
        },
    ]


@pytest.fixture
def mock_genai_client():
    """Mock Google GenAI client."""
    client = MagicMock()

    # Mock generate_content response
    mock_response = MagicMock()
    mock_response.text = "Sample generated content"
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].grounding_metadata = None

    client.models.generate_content = MagicMock(return_value=mock_response)
    client.models.generate_images = MagicMock(return_value=MagicMock(generated_images=[]))

    return client


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_config_dir(tmp_path) -> Path:
    """Temporary config directory with default.yaml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    yaml_content = """
gemini:
  models:
    deep_research: test-model
    pro: test-pro
    flash: test-flash
    image: test-image
  research:
    timeout_seconds: 60
    poll_interval_seconds: 5
"""
    (config_dir / "default.yaml").write_text(yaml_content)
    return config_dir
