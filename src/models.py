"""Data models for the workshop service monitoring tool."""

from datetime import datetime
from enum import Enum
from typing import List, Optional


class ServiceStatus(Enum):
    """Service status enumeration."""

    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServiceType(Enum):
    """Financial trading venue service types."""

    ORDER_MATCHING = "order-matching"
    MARKET_DATA = "market-data"
    RISK_MANAGEMENT = "risk-management"
    SETTLEMENT = "settlement"
    AUTHENTICATION = "authentication"
    FAX = "fax"
    POSITION_MANAGEMENT = "position-management"
    PRICE_DISCOVERY = "price-discovery"


class ClusterNode:
    """Represents a machine in the trading venue cluster."""

    def __init__(
        self,
        node_id: str,
        hostname: str,
        cpu_cores: int = 8,
        memory_gb: int = 32,
        is_active: bool = True,
    ):
        self.node_id = node_id
        self.hostname = hostname
        self.cpu_cores = cpu_cores
        self.memory_gb = memory_gb
        self.is_active = is_active
        self.services: List[str] = []  # Service names deployed on this node


class ServiceMetrics:
    """Service performance metrics."""

    def __init__(
        self,
        cpu_usage: float,
        memory_usage: float,
        memory_percentage: float,
        uptime_seconds: int,
        requests_per_second: float,
        response_time_p50: float,
        response_time_p95: float,
        response_time_p99: float,
        error_rate: float,
        queue_depth: int,
        active_connections: int,
        total_requests: int,
        total_errors: int,
        last_updated: Optional[datetime] = None,
        # Historical request tracking
        requests_1d: Optional[float] = None,
        requests_30d: Optional[float] = None,
        requests_6m: Optional[float] = None,
    ):
        self.cpu_usage = max(0, min(100, cpu_usage))
        self.memory_usage = max(0, memory_usage)
        self.memory_percentage = max(0, min(100, memory_percentage))
        self.uptime_seconds = max(0, uptime_seconds)
        self.requests_per_second = max(0, requests_per_second)
        self.response_time_p50 = max(0, response_time_p50)
        self.response_time_p95 = max(0, response_time_p95)
        self.response_time_p99 = max(0, response_time_p99)
        self.error_rate = max(0, min(100, error_rate))
        self.queue_depth = max(0, queue_depth)
        self.active_connections = max(0, active_connections)
        self.total_requests = max(0, total_requests)
        self.total_errors = max(0, total_errors)
        self.last_updated = last_updated or datetime.now()
        # Historical request data
        self.requests_1d = requests_1d
        self.requests_30d = requests_30d
        self.requests_6m = requests_6m


class ServiceConfig:
    """Service configuration."""

    def __init__(
        self,
        name: str,
        service_type: ServiceType,
        port: int,
        enabled: bool = True,
        cpu_range: tuple = (10.0, 80.0),
        memory_range: tuple = (256, 2048),
        max_connections: int = 1000,
        max_queue_depth: int = 100,
        dependencies: Optional[List[str]] = None,
        health_check_interval: int = 30,
        description: str = "",
        cluster_nodes: Optional[
            List[str]
        ] = None,  # Nodes where this service is deployed
        preferred_node: Optional[str] = None,  # Preferred deployment node
    ):
        self.name = name
        self.service_type = service_type
        self.port = max(1, min(65535, port))
        self.enabled = enabled
        self.cpu_range = cpu_range
        self.memory_range = memory_range
        self.max_connections = max_connections
        self.max_queue_depth = max_queue_depth
        self.dependencies = dependencies or []
        self.health_check_interval = health_check_interval
        self.description = description
        self.cluster_nodes = cluster_nodes or []
        self.preferred_node = preferred_node


class Service:
    """Represents a service in the trading venue."""

    def __init__(
        self,
        config: ServiceConfig,
        status: ServiceStatus = ServiceStatus.STOPPED,
        metrics: Optional[ServiceMetrics] = None,
        start_time: Optional[datetime] = None,
        pid: Optional[int] = None,
        version: str = "1.0.0",
        description: str = "",
    ):
        self.config = config
        self.status = status
        self.metrics = metrics
        self.start_time = start_time
        self.pid = pid
        self.version = version
        self.description = description or config.description

    def is_healthy(self) -> bool:
        """Check if service is healthy based on current metrics."""
        if self.status != ServiceStatus.RUNNING or not self.metrics:
            return False

        return (
            self.metrics.cpu_usage < 95.0
            and self.metrics.memory_percentage < 95.0
            and self.metrics.error_rate < 10.0
            and self.metrics.queue_depth < self.config.max_queue_depth
        )

    def get_uptime_display(self) -> str:
        """Get human-readable uptime string."""
        if not self.metrics:
            return "N/A"

        seconds = self.metrics.uptime_seconds
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert:
    """Service alert."""

    def __init__(
        self,
        service_name: str,
        level: AlertLevel,
        message: str,
        metric_name: str,
        current_value: float,
        threshold: float,
        timestamp: Optional[datetime] = None,
    ):
        self.service_name = service_name
        self.level = level
        self.message = message
        self.metric_name = metric_name
        self.current_value = current_value
        self.threshold = threshold
        self.timestamp = timestamp or datetime.now()

    def __str__(self) -> str:
        """String representation of alert."""
        return f"[{self.level.value.upper()}] {self.service_name}: {self.message}"


class SystemOverview:
    """Overall system status overview."""

    def __init__(
        self,
        total_services: int,
        running_services: int,
        stopped_services: int,
        error_services: int,
        total_cpu_usage: float,
        total_memory_usage: float,
        total_requests_per_second: float,
        average_response_time: float,
        total_active_connections: int,
        cluster_nodes: Optional[List[ClusterNode]] = None,
        alerts: Optional[List[Alert]] = None,
        last_updated: Optional[datetime] = None,
    ):
        self.total_services = total_services
        self.running_services = running_services
        self.stopped_services = stopped_services
        self.error_services = error_services
        self.total_cpu_usage = total_cpu_usage
        self.total_memory_usage = total_memory_usage
        self.total_requests_per_second = total_requests_per_second
        self.average_response_time = average_response_time
        self.total_active_connections = total_active_connections
        self.cluster_nodes = cluster_nodes or []
        self.alerts = alerts or []
        self.last_updated = last_updated or datetime.now()

    @property
    def health_percentage(self) -> float:
        """Calculate overall system health percentage."""
        if self.total_services == 0:
            return 100.0
        return (self.running_services / self.total_services) * 100.0

    @property
    def active_nodes(self) -> int:
        """Count of active cluster nodes."""
        return sum(1 for node in self.cluster_nodes if node.is_active)


# Copyright 2025 Bloomberg Finance L.P.
