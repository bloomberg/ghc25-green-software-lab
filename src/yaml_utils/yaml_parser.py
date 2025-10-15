"""
Simple YAML parser using only standard Python libraries.
Handles basic YAML structures commonly used in workshop configuration files.
"""

from typing import Dict, List, Union, Any


class SimpleYAMLParser:
    """A simple YAML parser using only standard Python libraries."""

    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """Parse a YAML file into a Python dictionary."""
        with open(file_path, "r") as f:
            content = f.read()
        return SimpleYAMLParser.parse_content(content)

    @staticmethod
    def parse_content(content: str) -> Dict[str, Any]:
        """Parse YAML content string into a Python dictionary."""
        lines = [line.rstrip("\n\r") for line in content.split("\n")]

        result = {}
        current_section = None
        current_list = None
        current_item = None

        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()

            if indent == 0 and ":" in stripped:
                # Top level key
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()

                if value:
                    result[key] = SimpleYAMLParser._parse_value(value)
                else:
                    result[key] = {}
                    current_section = result[key]
                current_list = None
                current_item = None

            elif indent == 2 and current_section is not None:
                if stripped.startswith("- "):
                    # List item
                    if current_list is None:
                        # Get the parent key name
                        parent_keys = list(result.keys())
                        if parent_keys:
                            parent_key = parent_keys[-1]
                            result[parent_key] = []
                            current_list = result[parent_key]
                            current_section = current_list

                    item_content = stripped[2:].strip()
                    if ":" in item_content:
                        # Object in list
                        key, value = item_content.split(":", 1)
                        key = key.strip()
                        value = value.strip()
                        current_item = {
                            key: (SimpleYAMLParser._parse_value(value) if value else {})
                        }
                        current_list.append(current_item)
                    else:
                        # Simple value in list
                        current_list.append(SimpleYAMLParser._parse_value(item_content))
                        current_item = None

                elif ":" in stripped:
                    # Regular key-value at level 2
                    key, value = stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if value:
                        current_section[key] = SimpleYAMLParser._parse_value(value)
                    else:
                        current_section[key] = {}

            elif indent == 4 and current_item is not None:
                # Properties of list items
                if ":" in stripped:
                    key, value = stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if value:
                        current_item[key] = SimpleYAMLParser._parse_value(value)
                    else:
                        current_item[key] = {}

            elif indent == 6 and current_item is not None:
                # Nested properties (like deployment.machines)
                if ":" in stripped:
                    key, value = stripped.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Find the parent key to nest under
                    parent_keys = list(current_item.keys())
                    if parent_keys:
                        parent_key = parent_keys[-1]
                        if not isinstance(current_item[parent_key], dict):
                            current_item[parent_key] = {}
                        current_item[parent_key][key] = SimpleYAMLParser._parse_value(
                            value
                        )

        return result

    @staticmethod
    def _parse_value(value: str) -> Union[str, int, float, bool, List[str]]:
        """Parse a YAML value into appropriate Python type."""
        if not value:
            return ""

        value = value.strip()

        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        # Handle lists in brackets
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            return [
                item.strip().strip('"').strip("'") for item in items if item.strip()
            ]

        # Handle booleans
        if value.lower() in ("true", "yes", "on"):
            return True
        elif value.lower() in ("false", "no", "off"):
            return False

        # Handle numbers
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Default to string
        return value


# Convenience functions for easy usage
def read_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a YAML file.

    This function replaces:
    try:
        import yaml
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
    """
    return SimpleYAMLParser.parse_file(file_path)


def parse_yaml_string(yaml_content: str) -> Dict[str, Any]:
    """Parse YAML content string into a Python dictionary."""
    return SimpleYAMLParser.parse_content(yaml_content)


# Copyright 2025 Bloomberg Finance L.P.
