"""Configuration management for the workshop service tool."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class MonitoringConfig:
    """Monitoring configuration settings."""

    def __init__(self):
        self.refresh_interval = 5
        self.alert_thresholds = {
            "cpu": 80.0,
            "memory": 85.0,
            "error_rate": 2.0,
            "queue_depth": 80.0,
        }
        self.max_history_points = 100


class DisplayConfig:
    """Display configuration settings."""

    def __init__(self):
        self.table_style = "simple"
        self.show_colors = True
        self.compact_mode = False
        self.precision = 2


class AppConfig:
    """Main application configuration."""

    def __init__(self):
        self.monitoring = MonitoringConfig()
        self.display = DisplayConfig()
        self.log_level = "INFO"
        self.data_dir = None


class ConfigManager:
    """Manages application configuration from multiple sources."""

    def __init__(self):
        self.config = AppConfig()
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from various sources in order of precedence."""
        # 1. Load from config file if it exists
        config_file = self._get_config_file_path()
        if config_file.exists():
            self._load_from_file(config_file)

        # 2. Override with environment variables
        self._load_from_env()

    def _get_config_file_path(self) -> Path:
        """Get the configuration file path."""
        # Check for config file in various locations
        possible_paths = [
            Path.cwd() / "workshop-svc.json",
            Path.cwd() / ".workshop-svc.json",
            Path.home() / ".workshop-svc" / "config.json",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Return default path (may not exist)
        return Path.home() / ".workshop-svc" / "config.json"

    def _load_from_file(self, config_file: Path) -> None:
        """Load configuration from JSON file."""
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            if config_data:
                # Update configuration with file data
                self._apply_config_data(config_data)
        except Exception as e:
            # If config file is invalid, use defaults
            print(f"Warning: Failed to load config from {config_file}: {e}")

    def _apply_config_data(self, config_data: Dict[str, Any]) -> None:
        """Apply configuration data to the config object."""
        if "monitoring" in config_data:
            monitoring = config_data["monitoring"]
            if "refresh_interval" in monitoring:
                self.config.monitoring.refresh_interval = monitoring["refresh_interval"]
            if "alert_thresholds" in monitoring:
                self.config.monitoring.alert_thresholds.update(
                    monitoring["alert_thresholds"]
                )
            if "max_history_points" in monitoring:
                self.config.monitoring.max_history_points = monitoring[
                    "max_history_points"
                ]

        if "display" in config_data:
            display = config_data["display"]
            if "table_style" in display:
                self.config.display.table_style = display["table_style"]
            if "show_colors" in display:
                self.config.display.show_colors = display["show_colors"]
            if "compact_mode" in display:
                self.config.display.compact_mode = display["compact_mode"]
            if "precision" in display:
                self.config.display.precision = display["precision"]

        if "log_level" in config_data:
            self.config.log_level = config_data["log_level"]

        if "data_dir" in config_data:
            self.config.data_dir = config_data["data_dir"]

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "WORKSHOP_SVC_REFRESH_INTERVAL": (
                "monitoring",
                "refresh_interval",
                int,
            ),
            "WORKSHOP_SVC_LOG_LEVEL": ("", "log_level", str),
            "WORKSHOP_SVC_DATA_DIR": ("", "data_dir", str),
            "WORKSHOP_SVC_COMPACT_MODE": (
                "display",
                "compact_mode",
                lambda x: x.lower() == "true",
            ),
            "WORKSHOP_SVC_SHOW_COLORS": (
                "display",
                "show_colors",
                lambda x: x.lower() == "true",
            ),
            "WORKSHOP_SVC_TABLE_STYLE": ("display", "table_style", str),
            "WORKSHOP_SVC_PRECISION": ("display", "precision", int),
        }

        for env_var, (section, key, converter) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    if section:
                        setattr(getattr(self.config, section), key, converted_value)
                    else:
                        setattr(self.config, key, converted_value)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid value for {env_var}: {value} ({e})")

        # Handle threshold environment variables
        threshold_prefixes = ["CPU", "MEMORY", "ERROR_RATE", "QUEUE_DEPTH"]
        for prefix in threshold_prefixes:
            env_var = f"WORKSHOP_SVC_ALERT_THRESHOLD_{prefix}"
            value = os.getenv(env_var)
            if value is not None:
                try:
                    threshold_value = float(value)
                    key = prefix.lower()
                    self.config.monitoring.alert_thresholds[key] = threshold_value
                except ValueError as e:
                    print(
                        f"Warning: Invalid threshold value for {env_var}: {value} ({e})"
                    )

    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        return self.config

    def save_config(self, file_path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if file_path is None:
            file_path = self._get_config_file_path()

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert config to dict for JSON serialization
        config_dict = {
            "monitoring": {
                "refresh_interval": self.config.monitoring.refresh_interval,
                "alert_thresholds": self.config.monitoring.alert_thresholds,
                "max_history_points": self.config.monitoring.max_history_points,
            },
            "display": {
                "table_style": self.config.display.table_style,
                "show_colors": self.config.display.show_colors,
                "compact_mode": self.config.display.compact_mode,
                "precision": self.config.display.precision,
            },
            "log_level": self.config.log_level,
            "data_dir": self.config.data_dir,
        }

        try:
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving config to {file_path}: {e}")

    def create_sample_config(self, file_path: Optional[Path] = None) -> None:
        """Create a sample configuration file."""
        if file_path is None:
            file_path = Path.home() / ".workshop-svc" / "config.json"

        sample_config = {
            "monitoring": {
                "refresh_interval": 5,
                "alert_thresholds": {
                    "cpu": 80.0,
                    "memory": 85.0,
                    "error_rate": 2.0,
                    "queue_depth": 80.0,
                },
                "max_history_points": 100,
            },
            "display": {
                "table_style": "simple",
                "show_colors": True,
                "compact_mode": False,
                "precision": 2,
            },
            "log_level": "INFO",
            "data_dir": None,
        }

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w") as f:
                json.dump(sample_config, f, indent=2)
            print(f"Sample configuration created at {file_path}")
        except Exception as e:
            print(f"Error creating sample config at {file_path}: {e}")


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get the current application configuration."""
    return config_manager.get_config()


def save_config(file_path: Optional[Path] = None) -> None:
    """Save the current configuration to file."""
    config_manager.save_config(file_path)


def create_sample_config(file_path: Optional[Path] = None) -> None:
    """Create a sample configuration file."""
    config_manager.create_sample_config(file_path)


# Copyright 2025 Bloomberg Finance L.P.
