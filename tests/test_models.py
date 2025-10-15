"""Tests for the models module."""

from datetime import datetime
from src.models import (
    ServiceStatus,
    ServiceMetrics,
    AlertLevel,
    Alert,
    SystemOverview,
)


def test_service_status_enum():
    """Test ServiceStatus enum values."""
    assert ServiceStatus.RUNNING.value == "running"
    assert ServiceStatus.STOPPED.value == "stopped"
    assert ServiceStatus.ERROR.value == "error"


def test_alert_level_enum():
    """Test AlertLevel enum values."""
    assert AlertLevel.INFO.value == "info"
    assert AlertLevel.WARNING.value == "warning"
    assert AlertLevel.CRITICAL.value == "critical"


def test_service_metrics_creation():
    """Test ServiceMetrics creation and validation."""
    metrics = ServiceMetrics(
        cpu_usage=50.0,
        memory_usage=1024,
        memory_percentage=60.0,
        uptime_seconds=3600,
        requests_per_second=100.0,
        response_time_p50=10.0,
        response_time_p95=50.0,
        response_time_p99=100.0,
        error_rate=0.5,
        queue_depth=5,
        active_connections=25,
        total_requests=10000,
        total_errors=50,
    )

    assert metrics.cpu_usage == 50.0
    assert metrics.memory_usage == 1024
    assert metrics.requests_per_second == 100.0
    assert isinstance(metrics.last_updated, datetime)


def test_alert_creation():
    """Test Alert creation."""
    alert = Alert(
        service_name="test-service",
        level=AlertLevel.WARNING,
        message="Test alert message",
        metric_name="cpu_usage",
        current_value=85.0,
        threshold=80.0,
    )

    assert alert.service_name == "test-service"
    assert alert.level == AlertLevel.WARNING
    assert alert.message == "Test alert message"
    assert isinstance(alert.timestamp, datetime)


def test_system_overview_creation():
    """Test SystemOverview creation."""
    overview = SystemOverview(
        total_services=5,
        running_services=4,
        stopped_services=1,
        error_services=0,
        total_cpu_usage=200.0,
        total_memory_usage=4096,
        total_requests_per_second=500.0,
        average_response_time=15.0,
        total_active_connections=100,
    )

    assert overview.total_services == 5
    assert overview.running_services == 4
    assert overview.health_percentage == 80.0  # 4/5 * 100
    assert overview.active_nodes == 0  # No cluster nodes provided


# Copyright 2025 Bloomberg Finance L.P.
