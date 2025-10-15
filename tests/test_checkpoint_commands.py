#!/usr/bin/env python3
"""
Test CLI checkpoint commands functionality.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cli import cmd_checkpoint


class TestCheckpointCommands(unittest.TestCase):
    """Test checkpoint command functionality."""

    def capture_output(self, func, args):
        """Helper to capture stdout output."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            func(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return output

    @patch("src.cli.create_service_manager_and_monitor")
    @patch("src.market_data_service.run_market_data_analysis")
    def test_checkpoint_2_run_market_data_success(
        self, mock_run_analysis, mock_create_manager
    ):
        """Test checkpoint 2 run-market-data command executes successfully."""
        # Setup mocks
        mock_service_manager = MagicMock()
        mock_monitor = MagicMock()
        mock_create_manager.return_value = (mock_service_manager, mock_monitor)

        # No fax service (checkpoint 1 complete)
        mock_service_manager.get_all_services.return_value = []

        # Create args
        args = argparse.Namespace(checkpoint="2", action="run-market-data")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify
        assert "🏦 Market Data Service - Checkpoint 2" in output
        assert "🐌 Running MARKET DATA SERVICE" in output
        mock_run_analysis.assert_called_once()

    @patch("src.cli.create_service_manager_and_monitor")
    def test_checkpoint_2_blocked_by_checkpoint_1(self, mock_create_manager):
        """Test checkpoint 2 is blocked when checkpoint 1 is not complete."""
        # Setup mocks - fax service still exists
        mock_service_manager = MagicMock()
        mock_monitor = MagicMock()
        mock_create_manager.return_value = (mock_service_manager, mock_monitor)

        mock_fax_service = MagicMock()
        mock_fax_service.config.name = "fax-service"
        mock_service_manager.get_all_services.return_value = [mock_fax_service]

        # Create args
        args = argparse.Namespace(checkpoint="2", action="run-market-data")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify checkpoint 2 is blocked
        assert "❌ Checkpoint 2 not available" in output
        assert "Complete Checkpoint 1 first" in output

    @patch("src.cli.create_service_manager_and_monitor")
    @patch("src.market_data_service.run_market_data_analysis")
    def test_checkpoint_2_handles_keyboard_interrupt(
        self, mock_run_analysis, mock_create_manager
    ):
        """Test checkpoint 2 handles keyboard interrupt gracefully."""
        # Setup mocks
        mock_service_manager = MagicMock()
        mock_monitor = MagicMock()
        mock_create_manager.return_value = (mock_service_manager, mock_monitor)
        mock_service_manager.get_all_services.return_value = []

        # Simulate keyboard interrupt
        mock_run_analysis.side_effect = KeyboardInterrupt()

        # Create args
        args = argparse.Namespace(checkpoint="2", action="run-market-data")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify graceful handling
        assert "⏹️  Execution interrupted" in output

    @patch("src.cli.create_service_manager_and_monitor")
    @patch("src.market_data_service.run_market_data_analysis")
    def test_checkpoint_2_handles_exception(
        self, mock_run_analysis, mock_create_manager
    ):
        """Test checkpoint 2 handles exceptions gracefully."""
        # Setup mocks
        mock_service_manager = MagicMock()
        mock_monitor = MagicMock()
        mock_create_manager.return_value = (mock_service_manager, mock_monitor)
        mock_service_manager.get_all_services.return_value = []

        # Simulate exception
        mock_run_analysis.side_effect = Exception("Test error")

        # Create args
        args = argparse.Namespace(checkpoint="2", action="run-market-data")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify error handling
        assert "❌ Error: Test error" in output

    def test_invalid_checkpoint_command(self):
        """Test invalid checkpoint command shows help message."""
        # Create args with invalid command
        args = argparse.Namespace(checkpoint="1", action="invalid-action")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify error message
        assert "❌ Invalid checkpoint command" in output
        assert "Available commands:" in output
        assert "python3 workshop.py checkpoint 2 run-market-data" in output

    def test_invalid_checkpoint_number(self):
        """Test invalid checkpoint number shows help message."""
        # Create args with invalid checkpoint
        args = argparse.Namespace(checkpoint="99", action="run-market-data")

        # Capture output
        output = self.capture_output(cmd_checkpoint, args)

        # Verify error message
        assert "❌ Invalid checkpoint command" in output


if __name__ == "__main__":
    unittest.main()
