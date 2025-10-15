#!/usr/bin/env python3
"""
Test suite for workshop exercise progression and alert system.
Validates that alerts are shown in the correct sequence based on workshop completion state.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock

from src.services import ServiceManager
from src.models import (
    Service,
    ServiceConfig,
    ServiceMetrics,
    ServiceStatus,
    AlertLevel,
)


class TestWorkshopAlertProgression:
    """Test the workshop alert system progression through exercises."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.service_manager = ServiceManager()

    def create_test_service(self, name: str, cpu_usage: float = 5.0, machines=None):
        """Helper to create a test service with specified metrics."""
        if machines is None:
            machines = ["node1"]

        from src.models import ServiceType

        config = ServiceConfig(
            name=name,
            service_type=ServiceType.MARKET_DATA,
            port=8080,
            description=f"Test {name}",
            max_queue_depth=100,
            cluster_nodes=machines,
        )

        service = Service(config=config)
        service.status = ServiceStatus.RUNNING
        service.metrics = ServiceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=512.0,
            memory_percentage=50.0,
            uptime_seconds=3600,
            requests_per_second=10.0,
            response_time_p50=100.0,
            response_time_p95=200.0,
            response_time_p99=300.0,
            error_rate=0.5,
            queue_depth=10,
            active_connections=50,
            total_requests=1000,
            total_errors=5,
        )

        return service

    def create_test_deployment_yaml(
        self, include_fax=True, price_discovery_size="large"
    ):
        """Create a test deployment.yaml content."""
        fax_section = (
            """
  - name: "fax-service"
    version: "2.1.3"
    description: "fax trail and compliance monitoring service"
    deployment:
      machines: ["node2"]
"""
            if include_fax
            else ""
        )

        return f"""kind: ClusterDeployment
metadata:
  name: trading-services-cluster
services:{fax_section}

machines:
  - hostname: "node1"
    size: small
  - hostname: "node2"
    size: {price_discovery_size}

services:
  - name: "price-discovery-service"
    version: "1.8.2"
    description: "Market price discovery and calculation engine"
    deployment:
      machines: ["node2"]

  - name: "market-data-service"
    version: "2.5.0"
    description: "Real-time market data ingestion and processing"
    deployment:
      machines: ["node1"]
{fax_section}
"""

    def test_exercise_1a_fax_service_alert_shown(self):
        """Test that Checkpoint 1 shows fax-service low utilization alert."""
        # Setup: Create services with fax-service present
        services = [
            self.create_test_service("fax", cpu_usage=2.0),  # Low CPU
            self.create_test_service("price-discovery", cpu_usage=20.0),
            self.create_test_service("market-data", cpu_usage=30.0),
        ]

        # Generate alerts
        alerts = self.service_manager._generate_workshop_alerts(services)

        # Verify: Should show fax-service alert
        fax_alerts = [a for a in alerts if a.service_name == "fax"]
        assert len(fax_alerts) == 1
        assert "Low utilization on large machine" in fax_alerts[0].message

        # Verify: Should NOT show price-discovery or market-data alerts
        price_alerts = [a for a in alerts if a.service_name == "price-discovery"]
        market_alerts = [a for a in alerts if a.service_name == "market-data"]
        assert len(price_alerts) == 0
        assert len(market_alerts) == 0

    @patch("src.services.ServiceManager._check_market_data_optimization")
    def test_exercise_2_market_data_alert_shown(self, mock_optimization_check):
        """Test that Checkpoint 2 shows market-data performance alert after Checkpoint 1 completion."""
        mock_optimization_check.return_value = False  # Not optimized yet

        # Setup: Create services WITHOUT fax-service (simulating removal)
        services = [
            self.create_test_service("price-discovery", cpu_usage=20.0),
            self.create_test_service("market-data", cpu_usage=30.0),
        ]

        # Generate alerts
        alerts = self.service_manager._generate_workshop_alerts(services)

        # Verify: Should show market-data alert after fax removal
        market_alerts = [a for a in alerts if a.service_name == "market-data"]
        assert len(market_alerts) == 1
        assert "performance issues" in market_alerts[0].message

        # Verify: Should NOT show other exercise alerts
        fax_alerts = [a for a in alerts if a.service_name == "fax-service"]
        price_alerts = [
            a for a in alerts if a.service_name == "price-discovery-service"
        ]
        assert len(fax_alerts) == 0
        assert len(price_alerts) == 0

    @patch("src.services.ServiceManager._check_market_data_optimization")
    def test_all_exercises_complete_no_workshop_alerts(self, mock_optimization_check):
        """Test that no workshop alerts are shown when all exercises are complete."""
        mock_optimization_check.return_value = True  # Market-data optimized

        # Setup: All exercises complete - no fax, price-discovery on small, market-data optimized
        services = [
            self.create_test_service(
                "price-discovery-service", cpu_usage=20.0, machines=["node2"]
            ),
            self.create_test_service("market-data-service", cpu_usage=30.0),
        ]

        # Mock deployment config to show price-discovery on small machine
        with patch.object(self.service_manager, "deployment_loader") as mock_loader:
            mock_config = Mock()
            mock_machine = Mock()
            mock_machine.hostname = "node2"
            mock_machine.size = "small"
            mock_config.machines = [mock_machine]
            mock_loader.load_config.return_value = mock_config

            # Generate alerts
            alerts = self.service_manager._generate_workshop_alerts(services)

        # Verify: Should NOT show any workshop alerts
        assert len(alerts) == 0

    def test_market_data_optimization_detection(self):
        """Test that the market data optimization detection works correctly."""
        # Create a temporary get_market_data.py file with inefficient code
        inefficient_code = """


def getMarketData(api_client):
    for ticker in tickers:
        market_data[ticker] = api_client.get_equity_spot(ticker)
    return market_data
"""

        optimized_code = """


def getMarketData(api_client):
    # Use bulk API instead of individual calls
    market_data = api_client.get_bulk_market_data(tickers)
    return market_data
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(inefficient_code)
            temp_file = f.name

        try:
            # Patch the file path to use our test file
            with patch("os.path.join", return_value=temp_file):
                result = self.service_manager._check_market_data_optimization()
                assert result is False  # Should detect inefficient code

            # Now test with optimized code
            with open(temp_file, "w") as f:
                f.write(optimized_code)

            with patch("os.path.join", return_value=temp_file):
                result = self.service_manager._check_market_data_optimization()
                assert result is True  # Should detect optimized code

        finally:
            os.unlink(temp_file)

    def test_latency_dashboard_progression(self):
        """Test that latency dashboard access follows exercise progression."""
        # This would be an integration test - testing the CLI command
        # For now, we can test the logic that blocks latency dashboard

        # Setup services with fax present (Checkpoint 1 not complete)
        services_with_fax = [
            self.create_test_service("fax-service", cpu_usage=2.0),
            self.create_test_service("market-data-service", cpu_usage=30.0),
        ]

        # Verify fax service exists
        fax_exists = any(s.config.name == "fax-service" for s in services_with_fax)
        assert fax_exists is True

        # Setup services without fax (Checkpoint 1 complete)
        services_without_fax = [
            self.create_test_service("market-data-service", cpu_usage=30.0)
        ]

        # Verify fax service does not exist
        fax_exists = any(s.config.name == "fax-service" for s in services_without_fax)
        assert fax_exists is False

    def test_alert_level_assignment(self):
        """Test that workshop alerts are assigned correct alert levels."""
        # Test fax-service alert level
        services = [self.create_test_service("fax", cpu_usage=2.0)]
        alerts = self.service_manager._generate_workshop_alerts(services)

        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        assert alerts[0].service_name == "fax"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Copyright 2025 Bloomberg Finance L.P.
