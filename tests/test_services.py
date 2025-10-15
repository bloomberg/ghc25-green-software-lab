"""Tests for the service management functionality."""

from src.services import ServiceManager, ServiceSimulator
from src.models import ServiceStatus


def test_service_manager_initialization():
    """Test ServiceManager initialization."""
    manager = ServiceManager()

    # Should have default services
    services = manager.get_all_services()
    assert len(services) > 0

    # Check that default services are created
    expected_services = [
        "market-data",
        "risk-management",
        "fax",
        "position-management",
        "price-discovery",
    ]

    service_names = [s.config.name for s in services]
    for expected in expected_services:
        assert expected in service_names


def test_get_service():
    """Test getting a specific service."""
    manager = ServiceManager()

    # Get existing service
    service = manager.get_service("fax")
    assert service is not None
    assert service.config.name == "fax"

    # Get non-existing service
    service = manager.get_service("non-existent")
    assert service is None


def test_get_running_services():
    """Test getting only running services."""
    manager = ServiceManager()

    # Initially all services should be running
    running_services = manager.get_running_services()
    all_services = manager.get_all_services()

    assert len(running_services) == len(all_services)

    # Stop a service and check again
    manager.stop_service("fax")
    running_services = manager.get_running_services()

    assert len(running_services) == len(all_services) - 1

    # Verify the stopped service is not in running list
    running_names = [s.config.name for s in running_services]
    assert "order-matching" not in running_names


def test_start_stop_service():
    """Test starting and stopping services."""
    manager = ServiceManager()

    # Stop a service
    result = manager.stop_service("fax")
    assert result is True

    service = manager.get_service("fax")
    assert service.status == ServiceStatus.STOPPED
    assert service.pid is None
    assert service.start_time is None
    assert service.metrics is None

    # Start the service again
    result = manager.start_service("fax")
    assert result is True

    service = manager.get_service("fax")
    assert service.status == ServiceStatus.RUNNING
    assert service.pid is not None
    assert service.start_time is not None
    assert service.metrics is not None

    # Try to start non-existent service
    result = manager.start_service("non-existent")
    assert result is False

    # Try to stop non-existent service
    result = manager.stop_service("non-existent")
    assert result is False


def test_update_all_metrics():
    """Test updating metrics for all services."""
    manager = ServiceManager()

    # Get initial metrics
    service = manager.get_service("fax")
    initial_metrics = service.metrics

    # Update all metrics
    manager.update_all_metrics()

    # Metrics should be updated (at least timestamp should be different)
    updated_service = manager.get_service("fax")
    updated_metrics = updated_service.metrics

    assert updated_metrics is not None
    assert updated_metrics.last_updated >= initial_metrics.last_updated


def test_get_system_overview():
    """Test getting system overview."""
    manager = ServiceManager()

    overview = manager.get_system_overview()

    assert overview.total_services > 0
    assert overview.running_services >= 0
    assert overview.stopped_services >= 0
    assert overview.error_services >= 0
    assert overview.total_services == (
        overview.running_services + overview.stopped_services + overview.error_services
    )

    # Health percentage should be between 0 and 100
    assert 0 <= overview.health_percentage <= 100


def test_service_simulator():
    """Test ServiceSimulator functionality."""
    manager = ServiceManager()
    service = manager.get_service("fax")

    simulator = ServiceSimulator(service)

    # Update metrics multiple times
    metrics1 = simulator.update_metrics()
    metrics2 = simulator.update_metrics()

    # Metrics should be valid
    assert 0 <= metrics1.cpu_usage <= 100
    assert metrics1.memory_usage > 0
    assert metrics1.requests_per_second >= 0
    assert metrics1.error_rate >= 0

    # Metrics should potentially change between updates
    # (though they might be the same due to randomness)
    assert metrics2.uptime_seconds >= metrics1.uptime_seconds


def test_alert_generation():
    """Test workshop alert generation for services."""
    manager = ServiceManager()

    # Get fax service - should generate workshop alert due to low CPU
    overview = manager.get_system_overview()

    # Should have workshop alerts
    alerts = overview.alerts
    assert len(alerts) > 0

    # Check that alerts contain workshop-specific information
    alert_messages = [alert.message for alert in alerts]
    assert any(
        "utilization" in msg.lower() or "performance" in msg.lower()
        for msg in alert_messages
    )


# Copyright 2025 Bloomberg Finance L.P.
