#!/usr/bin/env python3
"""
Workshop Checkpoint 3 Validation Test
Tests that risk calculation jobs have been rescheduled for carbon optimization

IMPORTANT: This test is DESIGNED TO FAIL initially and should pass after
attendees reschedule jobs to low-carbon periods and eliminate resource conflicts.

Usage:
    python3 workshop_validation/validate_checkpoint_3.py

Expected Behavior:
- At workshop start: FAILS (all jobs at 18:00, high carbon, resource conflicts)
- After Checkpoint 1, 2 only: FAILS (prerequisite check)
- After Checkpoint 3 completion: PASSES (jobs rescheduled to low-carbon periods)
"""

import sys
from pathlib import Path

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def load_deployment_yaml():
    """Load the deployment YAML configuration for prerequisite checks."""
    yaml_path = Path(__file__).parent.parent / "src/configuration_files/deployment.yaml"

    try:
        with open(yaml_path, "r") as f:
            content = f.read()

        services = []
        machines = []
        current_section = None

        for line in content.split("\n"):
            stripped = line.strip()

            if stripped == "services:":
                current_section = "services"
                continue
            elif stripped == "machines:" and not line.startswith("    "):
                current_section = "machines"
                continue
            elif stripped.startswith("monitoring:") and not stripped.startswith("  "):
                break

            if current_section == "services":
                if stripped.startswith("- name:"):
                    service_name = stripped.split(":", 1)[1].strip().strip("\"'")
                    services.append({"name": service_name})

            elif current_section == "machines":
                if stripped.startswith("- hostname:"):
                    hostname = stripped.split(":", 1)[1].strip().strip("\"'")
                    machines.append({"hostname": hostname})
                elif stripped.startswith("size:"):
                    size = stripped.split(":", 1)[1].strip().strip("\"'")
                    if machines:
                        machines[-1]["size"] = size

        return {"services": services, "machines": machines}

    except Exception:
        return None


def load_schedule_yaml():
    """Load the schedule YAML configuration."""
    yaml_path = Path(__file__).parent.parent / "src/configuration_files/schedule.yaml"

    try:
        with open(yaml_path, "r") as f:
            content = f.read()

        jobs = []
        current_job = None

        for line in content.split("\n"):
            stripped = line.strip()

            if stripped.startswith("jobs:"):
                continue
            elif stripped.startswith("- name:"):
                if current_job:
                    jobs.append(current_job)
                job_name = stripped.split(":", 1)[1].strip().strip("\"'")
                current_job = {"name": job_name}
            elif stripped.startswith("start_time:") and current_job:
                start_time = stripped.split(":", 1)[1].strip().strip("\"'")
                current_job["start_time"] = start_time
            elif stripped.startswith("duration_hours:") and current_job:
                duration = stripped.split(":", 1)[1].strip()
                current_job["duration_hours"] = float(duration)
            elif stripped.startswith("duration_minutes:") and current_job:
                duration = stripped.split(":", 1)[1].strip()
                current_job["duration_minutes"] = int(duration)

        if current_job:
            jobs.append(current_job)

        return {"jobs": jobs}

    except Exception as e:
        print(f"{RED}❌ ERROR: Could not load schedule.yaml: {e}{RESET}")
        return None


def check_market_data_optimization():
    """Check if get_market_data.py has been optimized."""
    market_data_file = Path(__file__).parent.parent / "src/get_market_data.py"

    try:
        with open(market_data_file, "r") as f:
            content = f.read()

        # Check for efficient patterns (should be active)
        efficient_patterns = [
            "api_client.get_bulk_market_data(",
            "get_bulk_market_data(tickers)",
        ]

        # Count active efficient patterns
        efficient_active = 0
        lines = content.split("\n")

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern in efficient_patterns:
                if pattern in line:
                    efficient_active += 1
                    break

        return efficient_active > 0

    except Exception:
        return False


def test_prerequisites_completed():
    """Check that Checkpoints 1 and 2 are completed first."""
    deployment = load_deployment_yaml()
    if deployment is None:
        return False, "Could not load deployment"

    services = deployment.get("services", [])

    # Check 1: fax-service removed
    fax_service_exists = any(
        service.get("name") == "fax-service" for service in services
    )
    if fax_service_exists:
        return False, "Checkpoint 1 not completed (fax-service still present)"

    # Check 2: market data service optimized
    if not check_market_data_optimization():
        return False, "Checkpoint 2 not completed (market data service not optimized)"

    return True, "Prerequisites satisfied"


def is_low_carbon_period(start_time_str):
    """Check if a given time is in the low-carbon period (2-6 AM)."""
    try:
        # Parse time string (format: "HH:MM" or "H:MM")
        time_parts = start_time_str.split(":")
        hour = int(time_parts[0])

        # Low carbon period is 2 AM to 6 AM (02:00 to 05:59)
        return 2 <= hour < 6

    except Exception:
        return False


def check_resource_conflicts(jobs):
    """
    Check if jobs have overlapping execution times causing resource conflicts.

    This function now uses the shared schedule_utils module to ensure
    consistent conflict detection between CLI and validation.
    """
    # Import the shared schedule utilities
    import sys
    from pathlib import Path

    # Add src directory to path to import shared utilities
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from yaml_utils import find_schedule_conflicts

    # Use the shared conflict detection function
    return find_schedule_conflicts(jobs)


def test_sustainable_batch_processing():
    """
    Test that risk calculation jobs have been optimized for sustainability

    Returns:
        bool: True if jobs are optimized (test passes), False otherwise
    """
    print(f"{BLUE}🧪 Checkpoint 4: Sustainable Batch Processing Test{RESET}")
    print("=" * 60)
    print("Validating that risk calculation jobs are scheduled in low-carbon periods")
    print()

    # Check prerequisites first
    prereqs_ok, prereq_msg = test_prerequisites_completed()
    if not prereqs_ok:
        print(f"{RED}❌ FAIL: Prerequisites not met{RESET}")
        print(f"{YELLOW}💡 {prereq_msg}{RESET}")
        print(f"{YELLOW}   Complete Checkpoints 1 and 2 first{RESET}")
        return False

    # Check job scheduling
    schedule = load_schedule_yaml()
    if schedule is None:
        print(f"{RED}❌ FAIL: Could not load job schedule configuration{RESET}")
        return False

    jobs = schedule.get("jobs", [])
    if not jobs:
        print(f"{RED}❌ FAIL: No jobs found in schedule.yaml{RESET}")
        return False

    # Check for resource conflicts (same start times)
    conflicts = check_resource_conflicts(jobs)
    if conflicts:
        print(
            f"{RED}❌ FAIL: Resource conflicts detected - jobs scheduled at same time{RESET}"
        )
        print(f"{YELLOW}💡 Conflicting jobs:{RESET}")
        for job1, job2 in conflicts:
            print(f"   • {job1} and {job2}")
        print()
        print(f"{YELLOW}📝 Solution: Stagger job start times in schedule.yaml{RESET}")
        return False

    # Check carbon optimization (jobs in low-carbon periods)
    high_carbon_jobs = []
    low_carbon_jobs = []

    for job in jobs:
        start_time = job.get("start_time", "")
        job_name = job.get("name", "unknown")

        if is_low_carbon_period(start_time):
            low_carbon_jobs.append(f"{job_name} ({start_time})")
        else:
            high_carbon_jobs.append(f"{job_name} ({start_time})")

    if high_carbon_jobs:
        print(f"{RED}❌ FAIL: Jobs still scheduled during high-carbon periods{RESET}")
        print(f"{YELLOW}💡 High-carbon jobs (need rescheduling):{RESET}")
        for job in high_carbon_jobs:
            print(f"   • {job}")
        print()
        print(
            f"{YELLOW}📝 Solution: Move jobs to low-carbon periods (2-6 AM) in schedule.yaml{RESET}"
        )
        return False

    # All checks passed
    print(f"{GREEN}✅ PASS: Risk calculation jobs successfully optimized{RESET}")
    print()
    print(f"{GREEN}🎉 Checkpoint 3 Complete!{RESET}")
    print("   • All jobs scheduled in low-carbon periods (2-6 AM)")
    print("   • No resource conflicts - jobs properly staggered")
    print(f"   • {len(low_carbon_jobs)} jobs optimized for sustainability:")
    for job in low_carbon_jobs:
        print(f"     - {job}")
    print()
    print(f"{BLUE}🏆 Workshop Complete! All exercises successfully finished!{RESET}")
    return True


def main():
    """Run Checkpoint 3 validation test."""
    print(f"{BLUE}🏦 WORKSHOP Checkpoint 3 VALIDATION{RESET}")
    print("=" * 60)
    print("This test validates sustainable optimization of batch processing jobs.")
    print("Expected to FAIL initially, PASS after completing Checkpoint 3.")
    print()

    success = test_sustainable_batch_processing()

    print("\n" + "=" * 60)
    if success:
        print(f"{GREEN}🏆 Checkpoint 3: COMPLETED{RESET}")
        return 0
    else:
        print(f"{RED}📋 Checkpoint 3: NOT YET COMPLETED{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Copyright 2025 Bloomberg Finance L.P.
