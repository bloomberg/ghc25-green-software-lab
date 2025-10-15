#!/usr/bin/env python3
"""
Test CLI integration for exercise-specific backup and restore functionality.
"""

import sys
import tempfile
import shutil
import argparse
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
from src.cli import cmd_backup

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLIBackupRestore(unittest.TestCase):
    """Test CLI integration for exercise-specific backup and restore."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_dir = self.test_dir / "configuration_files"
        self.backup_dir = self.config_dir / ".workshop_reference"

        # Create directories and files
        self.config_dir.mkdir(parents=True)
        self.backup_dir.mkdir(parents=True)

        # Create test files
        (self.config_dir / "deployment.yaml").write_text("current: deployment")
        (self.config_dir / "schedule.yaml").write_text("current: schedule")
        (self.backup_dir / "deployment_2.yaml").write_text("backup: 1b")
        (self.backup_dir / "deployment_2.yaml").write_text("backup: 2")
        (self.backup_dir / "schedule_original.yaml").write_text("backup: schedule")

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    @patch("src.cli.BackupManager")
    def test_cli_restore_checkpoint2_start(self, mock_manager_class):
        """Test CLI restore for checkpoint2-start."""
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.restore_exercise_state.return_value = True
        mock_manager_class.return_value = mock_manager

        # Create args object
        args = argparse.Namespace()
        args.action = "restore-checkpoint2-start"

        # Capture output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            cmd_backup(args)

        # Verify manager was called correctly
        mock_manager.restore_exercise_state.assert_called_once_with("checkpoint2-start")

        # Verify output
        output = mock_stdout.getvalue()
        self.assertIn("Restoring to Checkpoint 2 start state", output)

    @patch("src.cli.BackupManager")
    def test_cli_restore_checkpoint3_start(self, mock_manager_class):
        """Test CLI restore for checkpoint3-start."""
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.restore_exercise_state.return_value = True
        mock_manager_class.return_value = mock_manager

        # Create args object
        args = argparse.Namespace()
        args.action = "restore-checkpoint3-start"

        # Capture output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            cmd_backup(args)

        # Verify manager was called correctly
        mock_manager.restore_exercise_state.assert_called_once_with("checkpoint3-start")

        # Verify output
        output = mock_stdout.getvalue()
        self.assertIn("Restoring to Checkpoint 3 start state", output)

    @patch("src.cli.BackupManager")
    def test_cli_restore_checkpoint4_start_invalid(self, mock_manager_class):
        """Test CLI restore for checkpoint4-start - should show unknown action."""
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.restore_exercise_state.return_value = True
        mock_manager_class.return_value = mock_manager

        # Create args object
        args = argparse.Namespace()
        args.action = "restore-checkpoint5-start"

        # Capture output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            cmd_backup(args)

        # Verify manager was NOT called (checkpoint 5 has no restore point)
        mock_manager.restore_exercise_state.assert_not_called()

        # Verify output shows unknown restore action
        output = mock_stdout.getvalue()
        self.assertIn("Unknown restore action", output)

    @patch("src.cli.BackupManager")
    def test_cli_restore_failure(self, mock_manager_class):
        """Test CLI restore failure handling."""
        # Setup mock to return failure
        mock_manager = MagicMock()
        mock_manager.restore_exercise_state.return_value = False
        mock_manager_class.return_value = mock_manager

        # Create args object
        args = argparse.Namespace()
        args.action = "restore-checkpoint3-start"

        # Capture output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            cmd_backup(args)

        # Verify error message
        output = mock_stdout.getvalue()
        self.assertIn("Restore failed", output)

    @patch("src.cli.BackupManager")
    def test_cli_original_restore_still_works(self, mock_manager_class):
        """Test that original restore functionality is preserved."""
        # Setup mock
        mock_manager = MagicMock()
        mock_manager.restore_original.return_value = True
        mock_manager_class.return_value = mock_manager

        # Create args object
        args = argparse.Namespace()
        args.action = "restore-checkpoint1-start"

        # Capture output
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            cmd_backup(args)

        # Verify original restore was called
        mock_manager.restore_original.assert_called_once()

        # Verify output
        output = mock_stdout.getvalue()
        self.assertIn("Restarting to Checkpoint 1 start state", output)


if __name__ == "__main__":
    unittest.main()

# Copyright 2025 Bloomberg Finance L.P.
