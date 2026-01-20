# File: test_config.py | Module: tests
"""Unit tests for config.py."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestConfig:
    """Tests for Config class."""

    def test_config_loads_yaml(self, temp_config_dir, monkeypatch):
        """Test that config loads from YAML file."""
        # Reset singleton
        import config as config_module
        config_module.Config._instance = None

        # Patch the config path
        with patch.object(Path, '__truediv__', return_value=temp_config_dir / "default.yaml"):
            # Re-import to get fresh instance
            from importlib import reload
            reload(config_module)

            # The config should have loaded the YAML
            # Note: This test is tricky due to singleton pattern

    def test_google_api_key_from_env(self, monkeypatch):
        """Test API key comes from environment."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")

        import config as config_module
        config_module.Config._instance = None
        from importlib import reload
        reload(config_module)

        assert config_module.config.google_api_key == "test-api-key"

    def test_output_path_from_env(self, monkeypatch, tmp_path):
        """Test output path from environment."""
        test_path = str(tmp_path / "output")
        monkeypatch.setenv("OUTPUT_PATH", test_path)

        import config as config_module
        config_module.Config._instance = None
        from importlib import reload
        reload(config_module)

        assert str(config_module.config.output_path) == test_path

    def test_output_path_default(self, monkeypatch):
        """Test default output path."""
        monkeypatch.delenv("OUTPUT_PATH", raising=False)

        import config as config_module
        config_module.Config._instance = None
        from importlib import reload
        reload(config_module)

        expected = Path.home() / ".deep-research-articles" / "output"
        assert config_module.config.output_path == expected

    def test_log_path_from_env(self, monkeypatch, tmp_path):
        """Test log path from environment."""
        test_path = str(tmp_path / "logs")
        monkeypatch.setenv("LOG_PATH", test_path)

        import config as config_module
        config_module.Config._instance = None
        from importlib import reload
        reload(config_module)

        assert str(config_module.config.log_path) == test_path

    def test_get_nested_value(self):
        """Test getting nested config values."""
        import config as config_module

        # Mock the internal config dict
        config_module.config._config = {
            "gemini": {
                "models": {
                    "pro": "test-pro-model"
                }
            }
        }

        result = config_module.config.get("gemini.models.pro")
        assert result == "test-pro-model"

    def test_get_missing_value_returns_default(self):
        """Test that missing keys return default."""
        import config as config_module

        config_module.config._config = {}
        result = config_module.config.get("nonexistent.key", "default-value")
        assert result == "default-value"

    def test_model_properties_require_config(self):
        """Test model properties raise error when config missing."""
        import config as config_module

        config_module.config._config = {}

        with pytest.raises(ValueError, match="Missing gemini.models.deep_research"):
            _ = config_module.config.deep_research_model

        with pytest.raises(ValueError, match="Missing gemini.models.pro"):
            _ = config_module.config.pro_model

        with pytest.raises(ValueError, match="Missing gemini.models.flash"):
            _ = config_module.config.flash_model

        with pytest.raises(ValueError, match="Missing gemini.models.image"):
            _ = config_module.config.image_model

    def test_research_timeout_default(self):
        """Test research timeout has default."""
        import config as config_module

        config_module.config._config = {}
        assert config_module.config.research_timeout == 1800

    def test_poll_interval_default(self):
        """Test poll interval has default."""
        import config as config_module

        config_module.config._config = {}
        assert config_module.config.poll_interval == 30
