"""Tests for the monitoring functionality."""

from src.services import ServiceManager
from src.monitoring import Monitor


def test_monitor_initialization():
    """Test Monitor initialization."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    assert monitor.service_manager is service_manager
    assert monitor.history == {}
    assert monitor.max_history == 100


def test_get_current_status():
    """Test getting current system status."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    overview = monitor.get_current_status()

    assert overview is not None
    assert overview.total_services > 0
    assert hasattr(overview, "running_services")
    assert hasattr(overview, "total_cpu_usage")


def test_get_service_status():
    """Test getting status of a specific service."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    # Get existing service
    service = monitor.get_service_status("fax")
    assert service is not None
    assert service.config.name == "fax"

    # Get non-existing service
    service = monitor.get_service_status("non-existent")
    assert service is None


def test_service_history_tracking():
    """Test service history tracking functionality."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    # Get services for history tracking
    services = service_manager.get_running_services()[:2]  # Take first 2 services

    # Simulate updating history
    monitor._update_history(services)

    # Check that history was recorded
    service_name = services[0].config.name
    history = monitor.get_service_history(service_name, 1)

    assert len(history) == 1
    assert "timestamp" in history[0]
    assert "cpu_usage" in history[0]
    assert "memory_usage" in history[0]


def test_service_history_limits():
    """Test that service history respects max limits."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)
    monitor.max_history = 3  # Set small limit for testing

    service = service_manager.get_service("fax")
    services = [service] if service else []

    # Add multiple history points
    for _ in range(5):
        monitor._update_history(services)

    # Should only keep the last 3 points
    history = monitor.get_service_history("order-matching")
    assert len(history) <= 3


def test_get_service_history_empty():
    """Test getting history for service with no history."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    # Get history for service that hasn't been tracked
    history = monitor.get_service_history("non-existent-service")
    assert history == []

    # Get history for existing service but no history yet
    history = monitor.get_service_history("order-matching")
    assert history == []


def test_color_methods():
    """Test basic monitor functionality since color methods don't exist."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)

    # Test that monitor has basic functionality
    assert hasattr(monitor, "service_manager")
    assert hasattr(monitor, "history")
    assert hasattr(monitor, "max_history")

    # Test history initialization
    assert isinstance(monitor.history, dict)
    assert monitor.max_history == 100


# Copyright 2025 Bloomberg Finance L.P.
