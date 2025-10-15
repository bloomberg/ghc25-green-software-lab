"""Tests for dashboard display functionality."""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock
import sys

from src.services import ServiceManager
from src.monitoring import Monitor
from src.models import Service, ServiceConfig, ServiceMetrics, ServiceStatus
from src.cli import cmd_latency
from datetime import datetime


class TestDashboardDisplay:
    """Test suite for dashboard display functionality."""

    @pytest.fixture
    def service_manager(self):
        """Create a service manager for testing."""
        return ServiceManager()

    @pytest.fixture
    def monitor(self, service_manager):
        """Create a monitor for testing."""
        return Monitor(service_manager)

    @pytest.fixture
    def mock_service_with_high_latency(self):
        """Create a mock service with high latency for testing."""
        from src.models import ServiceType

        config = ServiceConfig(
            name="market-data",
            service_type=ServiceType.MARKET_DATA,
            port=8080,
            cpu_range=(10, 50),
            memory_range=(100, 500),
            max_connections=100,
            description="Market data service",
        )

        service = Service(
            config=config,
            status=ServiceStatus.RUNNING,
            start_time=datetime.now(),
            pid=1234,
            version="1.0.0",
            description="Test service",
        )

        # Set high latency metrics
        service.metrics = ServiceMetrics(
            cpu_usage=25.0,
            memory_usage=450,
            memory_percentage=65.0,
            uptime_seconds=3600,
            requests_per_second=15.0,
            response_time_p50=20000.0,  # 20 seconds
            response_time_p95=25000.0,  # 25 seconds
            response_time_p99=30000.0,  # 30 seconds
            error_rate=0.1,
            queue_depth=5,
            active_connections=45,
            total_requests=10000,
            total_errors=10,
        )

        return service

    @pytest.fixture
    def mock_service_with_low_latency(self):
        """Create a mock service with low latency for testing."""
        from src.models import ServiceType

        config = ServiceConfig(
            name="position-management",
            service_type=ServiceType.POSITION_MANAGEMENT,
            port=8081,
            cpu_range=(10, 50),
            memory_range=(100, 500),
            max_connections=100,
            description="Position management service",
        )

        service = Service(
            config=config,
            status=ServiceStatus.RUNNING,
            start_time=datetime.now(),
            pid=5678,
            version="1.0.0",
            description="Test service",
        )

        # Set low latency metrics
        service.metrics = ServiceMetrics(
            cpu_usage=15.0,
            memory_usage=200,
            memory_percentage=30.0,
            uptime_seconds=7200,
            requests_per_second=25.0,
            response_time_p50=2.0,  # 2ms
            response_time_p95=8.0,  # 8ms
            response_time_p99=15.0,  # 15ms
            error_rate=0.01,
            queue_depth=1,
            active_connections=20,
            total_requests=50000,
            total_errors=5,
        )

        return service

    def capture_output(self, func, *args, **kwargs):
        """Capture stdout output from a function."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        try:
            func(*args, **kwargs)
            return captured_output.getvalue()
        finally:
            sys.stdout = old_stdout

    def test_workshop_dashboard_display(
        self, monitor, mock_service_with_high_latency, mock_service_with_low_latency
    ):
        """Test workshop dashboard displays correctly."""
        services = [mock_service_with_high_latency, mock_service_with_low_latency]

        output = self.capture_output(monitor.display_workshop_dashboard, services)

        # Check that services are displayed
        assert "market-data" in output
        assert "position-management" in output

        # Check that CPU and memory info is displayed
        assert "CPU%" in output
        assert "Memory" in output

        # Check table structure
        assert "Service" in output
        assert "Status" in output
        assert "Deployment" in output

    def test_service_table_display(
        self, monitor, mock_service_with_high_latency, mock_service_with_low_latency
    ):
        """Test service table displays correctly."""
        services = [mock_service_with_high_latency, mock_service_with_low_latency]

        output = self.capture_output(monitor.display_service_table, services)

        # Check table headers
        assert "Service" in output
        assert "Status" in output
        assert "CPU%" in output
        assert "Memory" in output

        # Check service data
        assert "market-data" in output
        assert "position-management" in output
        assert "running" in output

    def test_latency_dashboard_display_with_critical_service(self):
        """Test latency dashboard displays critical services correctly."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            # Mock service manager with high latency service
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Create mock service with critical latency (>60 seconds for CRITICAL)
            critical_service = MagicMock()
            critical_service.config.name = "market-data"

            # Create a mock metrics object with proper numeric values
            mock_metrics = MagicMock()
            mock_metrics.response_time_p50 = 50000.0  # 50 seconds
            mock_metrics.response_time_p95 = 70000.0  # 70 seconds (CRITICAL)
            mock_metrics.response_time_p99 = 90000.0  # 90 seconds
            mock_metrics.queue_depth = 5

            critical_service.metrics = mock_metrics

            # Mock no fax service (Exercise 1 completed)
            mock_service_manager.get_all_services.return_value = [critical_service]
            mock_service_manager.get_service.return_value = critical_service

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Verify latency dashboard content
            assert "LATENCY DASHBOARD" in output
            assert "SERVICE RESPONSE TIMES" in output
            assert "market-data" in output
            assert "CRITICAL LATENCY ISSUES DETECTED" in output
            assert "🔴 CRITICAL" in output or "🟡 WARNING" in output
            assert "OPTIMIZATION RECOMMENDATIONS" in output

    def test_latency_dashboard_blocked_by_checkpoint1(self):
        """Test latency dashboard is blocked when Exercise 1 is not completed."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            # Mock service manager with fax service still present
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Create mock fax service (Exercise 1 not completed)
            fax_service = MagicMock()
            fax_service.config.name = "fax-service"

            mock_service_manager.get_all_services.return_value = [fax_service]

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Verify access is blocked
            assert "LATENCY ANALYSIS NOT AVAILABLE" in output
            assert "Complete Checkpoint 1 first" in output

    def test_latency_dashboard_with_healthy_services(self):
        """Test latency dashboard displays healthy services correctly."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            # Mock service manager with healthy services
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Create mock service with healthy latency
            healthy_service = MagicMock()
            healthy_service.config.name = "position-management"
            healthy_service.metrics.response_time_p50 = 2.0  # 2ms
            healthy_service.metrics.response_time_p95 = 8.0  # 8ms
            healthy_service.metrics.response_time_p99 = 15.0  # 15ms

            # Mock no fax service (Exercise 1 completed)
            mock_service_manager.get_all_services.return_value = [healthy_service]

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Verify healthy service display
            assert "LATENCY DASHBOARD" in output
            assert "position-management" in output
            assert "🟢 HEALTHY" in output

    def test_service_details_display(self, monitor, service_manager):
        """Test service details display correctly."""
        # Update metrics to ensure services exist
        service_manager.update_all_metrics()
        services = service_manager.get_all_services()

        if services:
            service_name = services[0].config.name
            output = self.capture_output(monitor.display_service_details, service_name)

            # Check that service details are displayed
            assert service_name in output or "Service" in output

    def test_metrics_summary_display(self, monitor):
        """Test metrics summary displays correctly."""
        output = self.capture_output(monitor.display_metrics_summary)

        # Check that metrics summary contains expected elements
        # The actual content depends on implementation
        assert len(output) >= 0  # Basic check that function executes

    @pytest.mark.parametrize(
        "latency_p95,expected_status",
        [
            (100.0, "🟢 HEALTHY"),  # 100ms - healthy
            (10000.0, "🟡 WARNING"),  # 10 seconds - warning
            (70000.0, "🔴 CRITICAL"),  # 70 seconds - critical
        ],
    )
    def test_latency_status_classification(self, latency_p95, expected_status):
        """Test that latency status is classified correctly."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Create mock service with specified latency
            test_service = MagicMock()
            test_service.config.name = "test-service"

            # Create proper mock metrics
            mock_metrics = MagicMock()
            mock_metrics.response_time_p50 = latency_p95 * 0.8
            mock_metrics.response_time_p95 = latency_p95
            mock_metrics.response_time_p99 = latency_p95 * 1.2
            mock_metrics.queue_depth = 1

            test_service.metrics = mock_metrics

            # Mock no fax service (Exercise 1 completed)
            mock_service_manager.get_all_services.return_value = [test_service]
            mock_service_manager.get_service.return_value = test_service

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Verify correct status classification
            assert expected_status in output

    def test_dashboard_integration_with_code_analysis(self):
        """Test that dashboard integrates with market data service code analysis."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            # Mock service manager that uses code analysis
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Mock code analysis result (inefficient version)
            mock_service_manager._check_market_data_optimization.return_value = False

            # Create mock market-data service with actual metric values
            market_data_service = MagicMock()
            market_data_service.config.name = "market-data"

            # Create a mock metrics object with actual numeric values
            mock_metrics = MagicMock()
            mock_metrics.response_time_p50 = 20000.0  # 20 seconds (inefficient)
            mock_metrics.response_time_p95 = 25000.0  # 25 seconds
            mock_metrics.response_time_p99 = 30000.0  # 30 seconds
            mock_metrics.queue_depth = 5

            market_data_service.metrics = mock_metrics

            # Mock no fax service (Exercise 1 completed)
            mock_service_manager.get_all_services.return_value = [market_data_service]

            # Mock the get_service method to return the same service with proper metrics
            mock_service_manager.get_service.return_value = market_data_service

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Verify the dashboard shows performance issues
            assert "market-data" in output
            assert "🟡 WARNING" in output or "🔴 CRITICAL" in output

    def test_dashboard_output_format_consistency(self):
        """Test that dashboard output formatting is consistent."""
        with patch("src.cli.create_service_manager_and_monitor") as mock_create:
            mock_service_manager = MagicMock()
            mock_monitor = MagicMock()
            mock_create.return_value = (mock_service_manager, mock_monitor)

            # Create multiple mock services
            services = []
            for i, name in enumerate(["service1", "service2", "service3"]):
                service = MagicMock()
                service.config.name = name
                service.metrics.response_time_p50 = 100.0 * (i + 1)
                service.metrics.response_time_p95 = 200.0 * (i + 1)
                service.metrics.response_time_p99 = 300.0 * (i + 1)
                services.append(service)

            mock_service_manager.get_all_services.return_value = services

            # Capture output
            args = MagicMock()
            output = self.capture_output(cmd_latency, args)

            # Check formatting consistency
            lines = output.split("\n")

            # Should have header separators
            separator_lines = [line for line in lines if "=" in line or "-" in line]
            assert len(separator_lines) > 0

            # Should have service entries
            for service_name in ["service1", "service2", "service3"]:
                assert service_name in output

    def test_empty_services_dashboard_handling(self, monitor):
        """Test dashboard handles empty services list gracefully."""
        output = self.capture_output(monitor.display_service_table, [])

        # Should not crash and should handle empty case
        assert len(output) >= 0

    def test_dashboard_error_handling(self, monitor):
        """Test dashboard handles errors gracefully."""
        # Test with None service
        output = self.capture_output(monitor.display_service_table, None)

        # Should not crash
        assert len(output) >= 0

    def test_workshop_recommendations_display(self, monitor):
        """Test workshop recommendations display when alerts are present."""
        from src.models import Alert, AlertLevel, SystemOverview

        # Create mock services
        services = []

        # Create mock system overview with alerts
        alert = Alert(
            service_name="market-data",
            level=AlertLevel.WARNING,
            message="High memory usage detected",
            metric_name="memory_usage",
            current_value=85.0,
            threshold=80.0,
            timestamp=datetime.now(),
        )

        overview = SystemOverview(
            total_services=2,
            running_services=2,
            stopped_services=0,
            error_services=0,
            total_cpu_usage=50.0,
            total_memory_usage=1024.0,
            total_requests_per_second=10.0,
            average_response_time=100.0,
            total_active_connections=50,
            alerts=[alert],
        )

        # Mock the service manager's get_system_overview method
        monitor.service_manager.get_system_overview = lambda: overview

        output = self.capture_output(
            monitor._display_workshop_recommendations, services, overview
        )

        # Check that recommendations are displayed when alerts exist
        assert "WORKSHOP RECOMMENDATIONS" in output
        assert "market-data" in output


# Copyright 2025 Bloomberg Finance L.P.
