#!/usr/bin/env python3
"""
Workshop Checkpoint 2 Validation Test
Tests that market-data-service code has been optimized to use bulk API

IMPORTANT: This test is DESIGNED TO FAIL initially and should pass after
attendees optimize the get_market_data.py code.

Usage:
    python3 workshop_validation/validate_checkpoint_2.py

Expected Behavior:
- At workshop start: FAILS (inefficient individual API calls)
- After Checkpoint 1 only: FAILS (prerequisite check)
- After Checkpoint 2 completion: PASSES (bulk API optimized code)
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
    """Load the deployment YAML configuration as JSON-compatible dict."""
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
            elif stripped == "machines:":
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


def test_prerequisites_completed():
    """Check that Checkpoint 1 is completed first."""
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

    return True, "Prerequisites satisfied"


def check_market_data_optimization():
    """Check if get_market_data.py has been optimized."""
    market_data_file = Path(__file__).parent.parent / "src/get_market_data.py"

    try:
        with open(market_data_file, "r") as f:
            content = f.read()

        # Check for inefficient patterns (should be commented out or removed)
        inefficient_patterns = [
            "for ticker in tickers:",
            "api_client.get_equity_spot(ticker)",
        ]

        efficient_patterns = [
            "api_client.get_bulk_market_data(",
            "get_bulk_market_data(tickers)",
        ]

        # Count active inefficient patterns (not commented)
        inefficient_active = 0
        efficient_active = 0

        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Check for inefficient patterns
            for pattern in inefficient_patterns:
                if pattern in line:
                    inefficient_active += 1
                    break

            # Check for efficient patterns
            for pattern in efficient_patterns:
                if pattern in line:
                    efficient_active += 1
                    break

        # Optimization is successful if:
        # - No active inefficient patterns OR
        # - At least one active efficient pattern
        is_optimized = (inefficient_active == 0) or (efficient_active > 0)

        return is_optimized, {
            "inefficient_active": inefficient_active,
            "efficient_active": efficient_active,
            "total_lines": len(lines),
        }

    except Exception as e:
        return False, f"Could not read get_market_data.py: {e}"


def test_market_data_optimization():
    """
    Test that market-data-service code has been optimized

    Returns:
        bool: True if code is optimized (test passes), False otherwise
    """
    print(f"{BLUE}🧪 Checkpoint 2: Market Data Service Optimization Test{RESET}")
    print("=" * 60)
    print("Validating that get_market_data.py uses efficient bulk API")
    print()

    # Check prerequisites first
    prereqs_ok, prereq_msg = test_prerequisites_completed()
    if not prereqs_ok:
        print(f"{RED}❌ FAIL: Prerequisites not met{RESET}")
        print(f"{YELLOW}💡 {prereq_msg}{RESET}")
        print(f"{YELLOW}   Complete Checkpoint 1 first{RESET}")
        return False

    # Check market data optimization
    is_optimized, details = check_market_data_optimization()

    if not is_optimized:
        print(
            f"{RED}❌ FAIL: get_market_data.py still uses inefficient individual API calls{RESET}"
        )
        print()
        print(f"{YELLOW}💡 To complete Checkpoint 2:{RESET}")
        print("   1. Open: src/get_market_data.py")
        print("   2. Find the MODIFICATION START/END section")
        print("   3. Comment out or remove the inefficient for loop")
        print("   4. Uncomment the bulk API call code")
        print("   5. Save the file and run this test again")
        print()
        print(f"{YELLOW}📝 Expected: Replace individual API calls with bulk API{RESET}")

        if isinstance(details, dict):
            print(f"{YELLOW}📊 Current code analysis:{RESET}")
            print(f"   • Inefficient patterns found: {details['inefficient_active']}")
            print(f"   • Efficient patterns found: {details['efficient_active']}")

        return False
    else:
        print(
            f"{GREEN}✅ PASS: get_market_data.py successfully optimized with bulk API{RESET}"
        )
        print()
        print(f"{GREEN}🎉 Checkpoint 2 Complete!{RESET}")
        print("   • Inefficient individual API calls removed")
        print("   • Bulk API implementation active")
        print("   • Response time improved from ~10s to <1s")
        print("   • Reduced server load and better user experience")
        print()
        print(
            f"{BLUE}➡️  Next: Continue to Checkpoint 3 (sustainable batch processing){RESET}"
        )
        return True


def main():
    """Run Checkpoint 2 validation test."""
    print(f"{BLUE}🏦 WORKSHOP Checkpoint 2 VALIDATION{RESET}")
    print("=" * 60)
    print("This test validates optimization of market-data-service code.")
    print("Expected to FAIL initially, PASS after completing Checkpoint 2.")
    print()

    success = test_market_data_optimization()

    print("\n" + "=" * 60)
    if success:
        print(f"{GREEN}🏆 Checkpoint 2: COMPLETED{RESET}")
        return 0
    else:
        print(f"{RED}📋 Checkpoint 2: NOT YET COMPLETED{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Copyright 2025 Bloomberg Finance L.P.
