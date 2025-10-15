"""
YAML validation utilities for workshop exercises.
Validates that manual edits to deployment.yaml meet exercise requirements.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .restore_files import BackupManager


class YAMLValidator:
    """Validates manual changes to deployment.yaml for workshop exercises."""

    def __init__(self, yaml_file_path: Optional[str] = None):
        self.backup_manager = BackupManager(yaml_file_path)
        self.yaml_file_path = self.backup_manager.get_yaml_file_path()
        self.original_backup_path = self.backup_manager.get_original_backup_path()

    def parse_services_from_yaml(self, file_path: str) -> List[Dict[str, any]]:
        """
        Parse services from YAML file using simple text parsing.
        Returns list of service dictionaries with name and other properties.
        """
        services = []

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Find services section
            services_section_match = re.search(r"^services:\s*$", content, re.MULTILINE)
            if not services_section_match:
                return services

            # Extract everything after "services:" line
            services_content = content[services_section_match.end() :]

            # Split by service entries (lines starting with "  - name:")
            service_blocks = re.split(
                r"^\s*- name:", services_content, flags=re.MULTILINE
            )[1:]

            for block in service_blocks:
                # Extract service name
                name_match = re.match(r'\s*["\']?([^"\':\s]+)["\']?', block)
                if name_match:
                    service_name = name_match.group(1)

                    # Extract other properties
                    service = {"name": service_name}

                    # Extract version
                    version_match = re.search(
                        r'^\s*version:\s*["\']?([^"\':\s]+)["\']?',
                        block,
                        re.MULTILINE,
                    )
                    if version_match:
                        service["version"] = version_match.group(1)

                    # Extract description
                    desc_match = re.search(
                        r'^\s*description:\s*["\']([^"\']*)["\']',
                        block,
                        re.MULTILINE,
                    )
                    if desc_match:
                        service["description"] = desc_match.group(1)

                    # Extract deployment machines
                    machines_match = re.search(
                        r"^\s*machines:\s*\[([^\]]+)\]", block, re.MULTILINE
                    )
                    if machines_match:
                        machines_str = machines_match.group(1)
                        machines = [m.strip(" \"'") for m in machines_str.split(",")]
                        service["machines"] = machines

                    services.append(service)

        except Exception as e:
            print(f"Error parsing YAML file {file_path}: {e}")

        return services

    def validate_service_removal(self, target_service: str) -> Tuple[bool, str]:
        """
        Validate that only the target service was removed from deployment.yaml.

        Returns:
            (success: bool, message: str)
        """
        # Ensure backup exists (this will create it automatically if needed)
        self.backup_manager._ensure_original_backup()

        if not Path(self.original_backup_path).exists():
            return (
                False,
                "❌ Original backup not found and could not be created automatically.",
            )

        if not Path(self.yaml_file_path).exists():
            return False, "❌ Current deployment.yaml not found."

        # Parse both files
        original_services = self.parse_services_from_yaml(self.original_backup_path)
        current_services = self.parse_services_from_yaml(self.yaml_file_path)

        # Extract service names
        original_names = {s["name"] for s in original_services}
        current_names = {s["name"] for s in current_services}

        # Check what was removed
        removed_services = original_names - current_names
        added_services = current_names - original_names

        # Validate removal
        if target_service not in original_names:
            return (
                False,
                f"❌ Target service '{target_service}' was not present in the original deployment.",
            )

        if len(removed_services) == 0:
            return (
                False,
                f"❌ No services were removed. Expected '{target_service}' to be removed.",
            )

        if len(removed_services) > 1:
            removed_list = ", ".join(sorted(removed_services))
            return (
                False,
                f"❌ Multiple services were removed: {removed_list}. Only '{target_service}' should be removed.",
            )

        if list(removed_services)[0] != target_service:
            actual_removed = list(removed_services)[0]
            return (
                False,
                f"❌ Wrong service removed. Expected '{target_service}', but '{actual_removed}' was removed.",
            )

        if len(added_services) > 0:
            added_list = ", ".join(sorted(added_services))
            return (
                False,
                f"❌ Unexpected services were added: {added_list}. Only removal was expected.",
            )

        # Validate that remaining services are unchanged
        for service in current_services:
            service_name = service["name"]
            original_service = next(
                (s for s in original_services if s["name"] == service_name),
                None,
            )

            if original_service is None:
                continue  # This shouldn't happen given our checks above

            # Check if key properties remain the same
            for key in ["version", "description"]:
                if key in original_service and key in service:
                    if original_service[key] != service[key]:
                        return (
                            False,
                            f"❌ Service '{service_name}' property '{key}' was modified. Expected only service removal.",
                        )

        return (
            True,
            f"✅ SUCCESS: Only '{target_service}' was removed from deployment.yaml. All other services remain unchanged.",
        )

    def validate_machine_size_change(
        self, service_name: str, expected_from_size: str, expected_to_size: str
    ) -> Tuple[bool, str]:
        """
        Validate that a service's machine size was changed correctly.

        Args:
            service_name: Name of the service to check
            expected_from_size: Expected original machine size (e.g., 'large')
            expected_to_size: Expected new machine size (e.g., 'small')
        """
        # Ensure backup exists
        self.backup_manager._ensure_original_backup()

        if not Path(self.original_backup_path).exists():
            return (
                False,
                "❌ Original backup file not found. Cannot validate changes.",
            )

        # Parse original and current deployments
        original_services = self.parse_services_from_yaml(self.original_backup_path)
        current_services = self.parse_services_from_yaml(self.yaml_file_path)

        # Find the target service in both versions
        original_service = next(
            (s for s in original_services if s["name"] == service_name), None
        )
        current_service = next(
            (s for s in current_services if s["name"] == service_name), None
        )

        if not original_service:
            return (
                False,
                f"❌ Service '{service_name}' not found in original deployment.",
            )

        if not current_service:
            return (
                False,
                f"❌ Service '{service_name}' not found in current deployment. Service may have been removed.",
            )

        # Extract machine information for the service
        original_machines = original_service.get("machines", [])
        current_machines = current_service.get("machines", [])

        if not original_machines:
            return (
                False,
                f"❌ No machine deployment found for '{service_name}' in original configuration.",
            )

        if not current_machines:
            return (
                False,
                f"❌ No machine deployment found for '{service_name}' in current configuration.",
            )

        # For this exercise, we expect the service to be deployed on the same machines but with different sizes
        # Check if machine sizes were updated correctly
        # We need to check the actual machine definitions, not just the service
        # deployment

        # Parse machine definitions from YAML files
        original_machine_sizes = self._parse_machine_sizes(self.original_backup_path)
        current_machine_sizes = self._parse_machine_sizes(self.yaml_file_path)

        # Get the machines this service is deployed to
        service_nodes = original_machines  # Should be same in both

        # Check each machine the service is deployed to
        size_changes = []
        for node in service_nodes:
            orig_size = original_machine_sizes.get(node, "unknown")
            curr_size = current_machine_sizes.get(node, "unknown")

            if orig_size != curr_size:
                size_changes.append(f"{node}: {orig_size} → {curr_size}")

        if not size_changes:
            return (
                False,
                f"❌ No machine size changes detected for '{service_name}'. Expected size change from '{expected_from_size}' to '{expected_to_size}'.",
            )

        # Check if the changes match expectations
        expected_change = f"{expected_from_size} → {expected_to_size}"
        actual_changes = ", ".join(size_changes)

        # Simple validation - check if we have the expected size change
        if (
            expected_to_size.lower() in actual_changes.lower()
            and expected_from_size.lower()
            not in current_machine_sizes.get(service_nodes[0], "").lower()
        ):
            return (
                True,
                f"✅ SUCCESS: Machine size changed for '{service_name}': {actual_changes}",
            )
        else:
            return (
                False,
                f"❌ Unexpected size change for '{service_name}'. Expected: {expected_change}, Actual: {actual_changes}",
            )

    def _parse_machine_sizes(self, file_path: str) -> Dict[str, str]:
        """Parse machine size definitions from YAML file."""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            machine_sizes = {}

            # Find machines section
            machines_section = re.search(r"^machines:\s*$", content, re.MULTILINE)
            if not machines_section:
                return machine_sizes

            # Extract machines section content
            machines_content = content[machines_section.end() :]

            # Stop at the next major section (services:)
            next_section = re.search(r"^services:\s*$", machines_content, re.MULTILINE)
            if next_section:
                machines_content = machines_content[: next_section.start()]

            # Parse each machine entry
            machine_blocks = re.findall(
                r'^\s*-\s*hostname:\s*["\']?([^"\':\s]+)["\']?.*?size:\s*([^\s\n]+)',
                machines_content,
                re.MULTILINE | re.DOTALL,
            )

            for hostname, size in machine_blocks:
                machine_sizes[hostname] = size.strip("\"'")

            return machine_sizes
        except Exception:
            return {}

    def validate_exercise_completion(
        self, exercise_number: int, **kwargs
    ) -> Tuple[bool, str]:
        """
        Validate completion of a specific exercise.

        Args:
            exercise_number: The exercise number (1, 2, etc.)
            **kwargs: Exercise-specific parameters
        """
        if exercise_number == 1:
            # Exercise 1: Service removal validation OR machine size change
            target_service = kwargs.get("target_service", "fax-service")

            # Check if this is Case A (fax-service removal) or Case B
            # (price-discovery rightsizing)
            if target_service == "fax-service":
                return self.validate_service_removal(target_service)
            elif target_service == "price-discovery-service":
                # Case B: Validate machine size change from large to small
                return self.validate_machine_size_change(
                    "price-discovery-service", "large", "small"
                )
            else:
                # Generic service removal
                return self.validate_service_removal(target_service)

        elif exercise_number == 2:
            # Checkpoint 2: Performance Optimization
            return self.validate_checkpoint_2()
        elif exercise_number == 3:
            # Checkpoint 3: Sustainable Batch Processing
            return self.validate_checkpoint_3()
        else:
            return (
                False,
                f"❌ Exercise {exercise_number} validation not yet implemented.",
            )

    def show_diff_summary(self) -> None:
        """
        Show a summary of differences between original and current deployment.yaml.
        """
        # Ensure backup exists (this will create it automatically if needed)
        self.backup_manager._ensure_original_backup()

        if not Path(self.original_backup_path).exists():
            print(
                "❌ Original backup not found and could not be created automatically."
            )
            return

        original_services = self.parse_services_from_yaml(self.original_backup_path)
        current_services = self.parse_services_from_yaml(self.yaml_file_path)

        original_names = {s["name"] for s in original_services}
        current_names = {s["name"] for s in current_services}

        removed_services = original_names - current_names
        added_services = current_names - original_names

        print("📊 YAML Changes Summary:")
        print("=" * 50)

        if removed_services:
            print(f"🗑️  Removed services: {', '.join(sorted(removed_services))}")
        else:
            print("🗑️  Removed services: None")

        if added_services:
            print(f"➕ Added services: {', '.join(sorted(added_services))}")
        else:
            print("➕ Added services: None")

        print(f"📈 Total services: {len(original_names)} → {len(current_names)}")
        print()

    def validate_checkpoint_2(self) -> Tuple[bool, str]:
        """Validate Checkpoint 2: Performance Optimization."""
        try:
            # Import the validation function
            import importlib.util

            # Navigate from src/yaml_utils/yaml_validator.py to workshop_validation/
            validation_file = (
                Path(__file__).parent.parent.parent
                / "workshop_validation"
                / "validate_checkpoint_2.py"
            )

            spec = importlib.util.spec_from_file_location(
                "validate_checkpoint_2", validation_file
            )
            if not spec or not spec.loader:
                return False, "❌ Could not load validation module"

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Call the validation function directly (suppress output)
            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                success = module.test_market_data_optimization()

            if success:
                return (
                    True,
                    "✅ Checkpoint 2 Complete! Market data service optimized for bulk API calls",
                )
            else:
                return (
                    False,
                    "❌ Prerequisites not met",
                )

        except Exception as e:
            return False, f"❌ Checkpoint 2 validation error: {str(e)}"

    def validate_checkpoint_3(self) -> Tuple[bool, str]:
        """Validate Checkpoint 3: Sustainable Batch Processing."""
        try:
            # Import the validation function
            import importlib.util

            # Navigate from src/yaml_utils/yaml_validator.py to workshop_validation/
            validation_file = (
                Path(__file__).parent.parent.parent
                / "workshop_validation"
                / "validate_checkpoint_3.py"
            )

            spec = importlib.util.spec_from_file_location(
                "validate_checkpoint_3", validation_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Call the validation function directly (suppress output)
                import io
                import contextlib

                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    success = module.test_sustainable_batch_processing()

                if success:
                    return (
                        True,
                        "✅ Checkpoint 3 Complete! All jobs scheduled in low-carbon periods with no resource conflicts",
                    )
                else:
                    return (
                        False,
                        "❌ Prerequisites not met",
                    )
            else:
                return False, "❌ Could not load validation module"

        except Exception as e:
            return False, f"❌ Checkpoint 3 validation error: {str(e)}"


# Copyright 2025 Bloomberg Finance L.P.
