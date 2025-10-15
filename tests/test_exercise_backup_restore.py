#!/usr/bin/env python3
"""
Test exercise-specific backup and restore functionality.
"""

import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from src.yaml_utils.restore_files import BackupManager

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestExerciseBackupRestore(unittest.TestCase):
    """Test exercise-specific backup and restore functionality."""

    def setUp(self):
        """Set up test environment with temporary directories."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / "configuration_files"
        self.backup_dir = self.config_dir / ".workshop_reference"

        # Create directories
        self.config_dir.mkdir(parents=True)
        self.backup_dir.mkdir(parents=True)

        # Create test files
        self.deployment_yaml = self.config_dir / "deployment.yaml"
        self.schedule_yaml = self.config_dir / "schedule.yaml"

        # Create initial deployment.yaml (current state)
        self.deployment_yaml.write_text(
            """kind: ClusterDeployment
services:
  - name: "current-service"
    version: "1.0.0"
"""
        )

        # Create initial schedule.yaml
        self.schedule_yaml.write_text(
            """kind: JobSchedule
jobs:
  - name: "current-job"
    start_time: "18:00"
"""
        )

        # Create backup files
        (self.backup_dir / "deployment_original.yaml").write_text(
            """kind: ClusterDeployment
services:
  - name: "original-service"
    version: "1.0.0"
  - name: "fax-service"
    version: "2.1.3"
"""
        )

        (self.backup_dir / "deployment_2.yaml").write_text(
            """kind: ClusterDeployment
services:
  - name: "after-checkpoint1-service"
    version: "1.0.0"
"""
        )

        (self.backup_dir / "schedule_original.yaml").write_text(
            """kind: JobSchedule
jobs:
  - name: "original-job"
    start_time: "18:00"
"""
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_restore_checkpoint2_start(self):
        """Test restoring to Checkpoint 2 starting state."""
        # Create manager and override its paths
        manager = BackupManager(str(self.deployment_yaml))
        manager.backup_dir = self.backup_dir
        manager.config_dir = self.config_dir
        manager.schedule_yaml_path = self.schedule_yaml

        # Test restore
        result = manager.restore_exercise_state("checkpoint2-start")

        # Verify result
        self.assertTrue(result)

        # Check file content was restored
        content = self.deployment_yaml.read_text()
        self.assertIn("after-checkpoint1-service", content)

    def test_restore_checkpoint3_start(self):
        """Test restoring to Checkpoint 3 starting state."""
        manager = BackupManager(str(self.deployment_yaml))
        manager.backup_dir = self.backup_dir
        manager.config_dir = self.config_dir
        manager.schedule_yaml_path = self.schedule_yaml

        # Test restore
        result = manager.restore_exercise_state("checkpoint3-start")

        # Verify result
        self.assertTrue(result)

        # Check deployment file content was restored
        deployment_content = self.deployment_yaml.read_text()
        self.assertIn("after-checkpoint1-service", deployment_content)

        # Check schedule file content was restored
        schedule_content = self.schedule_yaml.read_text()
        self.assertIn("original-job", schedule_content)

    def test_restore_invalid_exercise(self):
        """Test error handling for invalid exercise ID."""
        manager = BackupManager(str(self.deployment_yaml))
        manager.backup_dir = self.backup_dir

        # Test restore with invalid exercise
        result = manager.restore_exercise_state("invalid-exercise")

        # Verify result
        self.assertFalse(result)

    def test_restore_missing_backup(self):
        """Test error handling when backup file is missing."""
        manager = BackupManager(str(self.deployment_yaml))
        manager.backup_dir = self.backup_dir

        # Remove backup file
        (self.backup_dir / "deployment_2.yaml").unlink()

        # Test restore
        result = manager.restore_exercise_state("checkpoint2-start")

        # Verify result
        self.assertFalse(result)

    def test_backup_files_exist(self):
        """Test that all required backup files exist in the reference directory."""
        # This tests the actual backup files in the real project
        actual_backup_dir = (
            Path(__file__).parent.parent
            / "src"
            / "configuration_files"
            / ".workshop_reference"
        )

        required_files = [
            "deployment_original.yaml",
            "deployment_2.yaml",
            "schedule_original.yaml",
        ]

        for filename in required_files:
            backup_file = actual_backup_dir / filename
            self.assertTrue(
                backup_file.exists(), f"Required backup file missing: {filename}"
            )

            # Verify file has content
            content = backup_file.read_text().strip()
            self.assertTrue(len(content) > 0, f"Backup file is empty: {filename}")


if __name__ == "__main__":
    unittest.main()

# Copyright 2025 Bloomberg Finance L.P.
