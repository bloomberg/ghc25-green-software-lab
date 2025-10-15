"""
YAML backup and restoration utilities for workshop exercises.
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional


class BackupManager:
    """Manages backup and restoration of deployment.yaml and schedule.yaml for workshop exercises."""

    def __init__(self, yaml_file_path: Optional[str] = None):
        if yaml_file_path is None:
            base_path = (
                Path(__file__).parent.parent / "configuration_files" / "deployment.yaml"
            )
            yaml_file_path = str(base_path)

        self.yaml_file_path = yaml_file_path
        self.config_dir = Path(__file__).parent.parent / "configuration_files"
        self.schedule_yaml_path = self.config_dir / "schedule.yaml"
        self.get_market_data_path = Path(__file__).parent.parent / "get_market_data.py"

        # Store backups in a hidden reference folder
        self.backup_dir = (
            Path(__file__).parent.parent / "configuration_files" / ".workshop_reference"
        )
        self.backup_dir.mkdir(exist_ok=True)
        self.original_backup_path = self.backup_dir / "deployment_original.yaml"
        self.schedule_original_backup_path = self.backup_dir / "schedule_original.yaml"
        self.get_market_data_backup_path = (
            self.backup_dir / "get_market_data_original.py"
        )

        self.get_market_data_optimized_backup_path = (
            self.backup_dir / "get_market_data_optimized.py"
        )

        # Automatically create original backups if they don't exist
        self._ensure_original_backup()

    def _ensure_original_backup(self) -> None:
        """
        Automatically create original backups if they don't exist.
        This runs silently in the background and ONLY creates the backup once.
        Once created, the original backups are never overwritten to preserve the true initial state.
        """
        # Backup deployment.yaml
        if (
            not self.original_backup_path.exists()
            and Path(self.yaml_file_path).exists()
        ):
            try:
                shutil.copy2(self.yaml_file_path, self.original_backup_path)
                # Silent operation - no user output needed
            except Exception:
                # Fail silently - validation will handle missing backup
                # gracefully
                pass

        # Backup schedule.yaml
        if (
            not self.schedule_original_backup_path.exists()
            and self.schedule_yaml_path.exists()
        ):
            try:
                shutil.copy2(
                    self.schedule_yaml_path, self.schedule_original_backup_path
                )
                # Silent operation - no user output needed
            except Exception:
                # Fail silently - validation will handle missing backup
                # gracefully
                pass

        # Backup get_market_data.py
        if (
            not self.get_market_data_backup_path.exists()
            and self.get_market_data_path.exists()
        ):
            try:
                shutil.copy2(
                    self.get_market_data_path, self.get_market_data_backup_path
                )
                # Silent operation - no user output needed
            except Exception:
                # Fail silently - validation will handle missing backup
                # gracefully
                pass

    def create_checkpoint_backup(self, checkpoint_name: str = None) -> str:
        """
        Create a timestamped backup of the current deployment.yaml.
        Useful for creating restore points during exercises.
        """
        if checkpoint_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_name = f"checkpoint_{timestamp}"

        backup_path = self.backup_dir / f"deployment_{checkpoint_name}.yaml"

        try:
            shutil.copy2(self.yaml_file_path, backup_path)
            print(f"✅ Checkpoint backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"❌ Failed to create checkpoint backup: {e}")
            return ""

    def restore_original(self) -> bool:
        """
        Restore the original deployment.yaml from backup.
        """
        try:
            # Ensure backup exists before attempting restore
            self._ensure_original_backup()
            python_backup = self.get_market_data_backup_path
            schedule_backup = self.backup_dir / "schedule_original.yaml"

            if self.original_backup_path.exists():
                shutil.copy2(self.original_backup_path, self.yaml_file_path)
                print("✅ Successfully restored original deployment.yaml")
            else:
                print("❌ Original backup not found")
                print("   Unable to restore - original configuration may be lost")
                return False

            if python_backup.exists():
                shutil.copy2(python_backup, self.get_market_data_path)
                print("✅ Successfully restored get_market_data.py")
            else:
                print("❌ Checkpoint 2 Python code backup not found")
                return False

            if schedule_backup.exists():
                shutil.copy2(schedule_backup, self.schedule_yaml_path)
                print("✅ Successfully restored schedule.yaml")
            else:
                print("❌ Checkpoint 3 schedule backup not found")
                return False
        except Exception as e:
            print(f"❌ Failed to restore original deployment.yaml: {e}")
            return False

    def reset_original_backup(self) -> bool:
        """
        INSTRUCTOR USE ONLY: Force recreate the original backup from current state.
        This overwrites the existing original backup - use with caution!
        """
        try:
            if self.original_backup_path.exists():
                print("⚠️  WARNING: This will overwrite the existing original backup!")
                print(f"   Current backup: {self.original_backup_path}")
                confirm = input("   Type 'RESET' to confirm: ")
                if confirm != "RESET":
                    print("   Operation cancelled")
                    return False

            shutil.copy2(self.yaml_file_path, self.original_backup_path)
            print("✅ Original backup reset from current deployment.yaml state")
            return True
        except Exception as e:
            print(f"❌ Failed to reset original backup: {e}")
            return False

    def list_backups(self) -> None:
        """
        List all available backups.
        """
        if not self.backup_dir.exists():
            print("📂 No backup directory found")
            return

        backups = list(self.backup_dir.glob("*.yaml"))
        if not backups:
            print("📂 No backups found")
            return

        print("📂 Available backups:")
        for backup in sorted(backups):
            size = backup.stat().st_size
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            print(
                f"   • {backup.name} ({size} bytes, modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})"
            )

    def get_yaml_file_path(self) -> str:
        """Get the path to the deployment.yaml file."""
        return self.yaml_file_path

    def get_original_backup_path(self) -> str:
        """Get the path to the original backup file."""
        return str(self.original_backup_path)

    def restore_exercise_state(self, exercise_id: str) -> bool:
        """
        Restore configuration to a specific exercise state.

        Args:
            exercise_id: One of 'checkpoint2-start', 'checkpoint3-start'

        Returns:
            bool: True if restore successful, False otherwise
        """
        try:
            if exercise_id == "checkpoint2-start":
                # Restore to state after Checkpoint 1 (fax-service removed)
                # Also restore get_market_data.py to inefficient state
                deployment_backup = self.backup_dir / "deployment_2.yaml"
                python_backup = self.get_market_data_backup_path
                schedule_backup = self.backup_dir / "schedule_original.yaml"

                success = True
                if deployment_backup.exists():
                    shutil.copy2(deployment_backup, self.yaml_file_path)
                else:
                    print("❌ Checkpoint 2 deployment backup not found")
                    success = False

                if python_backup.exists():
                    shutil.copy2(python_backup, self.get_market_data_path)
                else:
                    print("❌ Checkpoint 2 Python code backup not found")
                    success = False

                if schedule_backup.exists():
                    shutil.copy2(schedule_backup, self.schedule_yaml_path)
                else:
                    print("❌ Checkpoint 3 schedule backup not found")
                    success = False

                if success:
                    print("✅ Restored to Checkpoint 2 starting state")
                    print("   • fax-service removed")
                    print("   • get_market_data.py reset to inefficient code")
                    print("   • Ready to optimize performance")
                    return True
                else:
                    return False

            elif exercise_id == "checkpoint3-start":
                # Restore to state after Checkpoint 2 (deployment + original schedule)
                deployment_backup = self.backup_dir / "deployment_2.yaml"
                schedule_backup = self.backup_dir / "schedule_original.yaml"
                python_optimized_backup = self.get_market_data_optimized_backup_path

                success = True
                if deployment_backup.exists():
                    shutil.copy2(deployment_backup, self.yaml_file_path)
                else:
                    print("❌ Checkpoint 3 deployment backup not found")
                    success = False

                if python_optimized_backup.exists():
                    shutil.copy2(python_optimized_backup, self.get_market_data_path)
                else:
                    print("❌ Checkpoint 3 Python code backup not found")
                    success = False

                if schedule_backup.exists():
                    shutil.copy2(schedule_backup, self.schedule_yaml_path)
                else:
                    print("❌ Checkpoint 3 schedule backup not found")
                    success = False

                if success:
                    print("✅ Restored to Checkpoint 3 starting state")
                    print("   • All optimizations preserved")
                    print("   • Original schedule.yaml restored")
                    print("   • Ready to optimize job scheduling")
                    return True
                else:
                    return False

            else:
                print(f"❌ Unknown checkpoint ID: {exercise_id}")
                return False

        except Exception as e:
            print(f"❌ Failed to restore checkpoint state '{exercise_id}': {e}")
            return False


# Copyright 2025 Bloomberg Finance L.P.
