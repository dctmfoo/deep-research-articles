# File: config.py | Module: mcp-server
"""Configuration loader for the Deep Research Articles MCP server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager for the MCP server."""

    _instance: Config | None = None
    _config: dict[str, Any]

    def __new__(cls) -> Config:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        config_path = Path(__file__).parent.parent / "config" / "default.yaml"
        
        if config_path.exists():
            with open(config_path) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value

    @property
    def google_api_key(self) -> str:
        """Get Google API key from environment or config."""
        return os.environ.get("GOOGLE_API_KEY", "")

    @property
    def output_path(self) -> Path:
        """Get output path for artifacts."""
        path = os.environ.get("OUTPUT_PATH", "")
        if path:
            return Path(path)
        return Path.home() / ".deep-research-articles" / "output"

    @property
    def log_path(self) -> Path:
        """Get log path."""
        path = os.environ.get("LOG_PATH", "")
        if path:
            return Path(path)
        return Path.home() / ".deep-research-articles" / "logs"

    @property
    def deep_research_model(self) -> str:
        """Get deep research model name from config/default.yaml."""
        model = self.get("gemini.models.deep_research")
        if not model:
            raise ValueError("Missing gemini.models.deep_research in config")
        return model

    @property
    def pro_model(self) -> str:
        """Get Gemini Pro model name from config/default.yaml."""
        model = self.get("gemini.models.pro")
        if not model:
            raise ValueError("Missing gemini.models.pro in config")
        return model

    @property
    def flash_model(self) -> str:
        """Get Gemini Flash model name from config/default.yaml."""
        model = self.get("gemini.models.flash")
        if not model:
            raise ValueError("Missing gemini.models.flash in config")
        return model

    @property
    def image_model(self) -> str:
        """Get image generation model name from config/default.yaml."""
        model = self.get("gemini.models.image")
        if not model:
            raise ValueError("Missing gemini.models.image in config")
        return model

    @property
    def research_timeout(self) -> int:
        """Get research timeout in seconds."""
        return self.get("gemini.research.timeout_seconds", 1800)

    @property
    def poll_interval(self) -> int:
        """Get polling interval in seconds."""
        return self.get("gemini.research.poll_interval_seconds", 30)


# Singleton instance
config = Config()
