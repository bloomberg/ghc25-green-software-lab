"""
YAML utilities package for workshop-svc.

The helper functions defined in this package are implemented locally for the purposes of the workshop.
They are provided solely to avoid external dependencies and to keep the workshop environment self-contained.
These functions are for illustration and convenience only and are not intended for production use or general distribution.
"""

from .yaml_parser import SimpleYAMLParser, read_yaml_file, parse_yaml_string
from .restore_files import BackupManager
from .yaml_validator import YAMLValidator
from .schedule_utils import (
    parse_time_to_minutes,
    get_job_duration_minutes,
    check_jobs_overlap,
    find_schedule_conflicts,
)

__all__ = [
    "SimpleYAMLParser",
    "read_yaml_file",
    "parse_yaml_string",
    "BackupManager",
    "YAMLValidator",
    "parse_time_to_minutes",
    "get_job_duration_minutes",
    "check_jobs_overlap",
    "find_schedule_conflicts",
]

# Copyright 2025 Bloomberg Finance L.P.
