#!/usr/bin/env python3
"""
Workshop Part 1A Validation Test
Tests that fax-service has been removed from deployment.yaml

IMPORTANT: This test is DESIGNED TO FAIL initially and should pass after
attendees remove fax-service from deployment.yaml

Usage:
    python3 workshop_validation/validate_checkpoint_1.py

Expected Behavior:
- At workshop start: FAILS (fax-service present)
- After Checkpoint 1 completion: PASSES (fax-service removed)
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
        # Read YAML file as text and parse manually (avoiding PyYAML dependency)
        with open(yaml_path, "r") as f:
            content = f.read()

        # Simple YAML parsing for our specific structure
        # Look for service entries under 'services:' section
        services = []
        in_services_section = False
        current_service = None

        for line in content.split("\n"):
            stripped = line.strip()

            if stripped == "services:":
                in_services_section = True
                continue

            if in_services_section:
                if stripped.startswith("- name:"):
                    # Extract service name
                    service_name = stripped.split(":", 1)[1].strip().strip("\"'")
                    current_service = {"name": service_name}
                    services.append(current_service)
                elif stripped.startswith("monitoring:") and not stripped.startswith(
                    "  "
                ):
                    # End of services section
                    break

        return {"services": services}

    except Exception as e:
        print(f"{RED}❌ ERROR: Could not load deployment.yaml: {e}{RESET}")
        return None


def test_fax_service_removal():
    """
    Test that fax-service has been removed from deployment.yaml

    Returns:
        bool: True if fax-service is removed (test passes), False otherwise
    """
    print(f"{BLUE}🧪 Checkpoint 1: fax Service Removal Test{RESET}")
    print("=" * 60)
    print("Validating that fax-service has been removed from deployment.yaml")
    print()

    deployment = load_deployment_yaml()
    if deployment is None:
        print(f"{RED}❌ FAIL: Could not load deployment configuration{RESET}")
        return False

    # Check if fax-service exists in services list
    services = deployment.get("services", [])
    fax_service_exists = any(
        service.get("name") == "fax-service" for service in services
    )

    if fax_service_exists:
        print(f"{RED}❌ FAIL: fax-service still present in deployment.yaml{RESET}")
        print()
        print(f"{YELLOW}💡 To complete Checkpoint 1:{RESET}")
        print("   1. Open: src/configuration_files/deployment.yaml")
        print("   2. Find the fax-service entry in the services list")
        print("   3. Remove the entire fax-service section")
        print("   4. Save the file and run this test again")
        print()
        print(f"{YELLOW}📝 Expected: fax-service entry completely removed{RESET}")
        return False
    else:
        print(
            f"{GREEN}✅ PASS: fax-service successfully removed from deployment.yaml{RESET}"
        )
        print()
        print(f"{GREEN}🎉 Checkpoint 1 Complete!{RESET}")
        print("   • fax-service has been removed from deployment")
        print("   • This frees up machine resources")
        print("   • The dormant service is no longer consuming resources")
        print()
        print(
            f"{BLUE}➡️  Next: Continue to Checkpoint 2 (market-data optimization){RESET}"
        )
        return True


def main():
    """Run Checkpoint 1 validation test."""
    print(f"{BLUE}🏦 WORKSHOP Checkpoint 1 VALIDATION{RESET}")
    print("=" * 60)
    print("This test validates removal of the dormant fax-service.")
    print("Expected to FAIL initially, PASS after completing Checkpoint 1.")
    print()

    success = test_fax_service_removal()

    print("\n" + "=" * 60)
    if success:
        print(f"{GREEN}🏆 Checkpoint 1: COMPLETED{RESET}")
        return 0
    else:
        print(f"{RED}📋 Checkpoint 1: NOT YET COMPLETED{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Copyright 2025 Bloomberg Finance L.P.
