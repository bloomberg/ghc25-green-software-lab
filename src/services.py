"""Service simulation and management."""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .cluster_config import DeploymentLoader
from .models import (
    Alert,
    AlertLevel,
    ClusterNode,
    Service,
    ServiceMetrics,
    ServiceStatus,
    SystemOverview,
)


class ServiceSimulator:
    """Simulates realistic service behavior and metrics."""

    def __init__(self, service: Service):
        self.service = service
        self._base_metrics = self._generate_base_metrics()
        self._start_time = datetime.now()

    def _generate_base_metrics(self) -> ServiceMetrics:
        """Generate baseline metrics for the service."""
        config = self.service.config

        # Generate realistic baseline values based on workshop scenarios
        if config.name == "fax":
            # fax service: very low CPU to trigger workshop alert
            cpu_base = random.uniform(0.5, 2.5)
        elif config.name == "price-discovery":
            # Price-discovery: low utilization to trigger workshop alert after
            # fax removal
            cpu_base = random.uniform(8, 16)
        elif config.name == "market-data":
            # Market-data service: high CPU usage
            cpu_base = random.uniform(70, 85)
        elif config.name == "position-management":
            # Position-management service: high CPU usage
            cpu_base = random.uniform(70, 85)
        elif config.name == "risk-management":
            # Risk-management service: high CPU usage
            cpu_base = random.uniform(75, 80)
        else:
            # Other services: safe CPU range to avoid any alerts
            cpu_base = random.uniform(30, 70)  # Safe range, won't trigger alerts

        memory_base = random.randint(*config.memory_range)

        # Fix potential issue with max_connections being too small
        max_conn_half = max(1, config.max_connections // 2)
        active_conn_min = min(50, max_conn_half)

        # Workshop-specific request patterns (using service names without
        # -service suffix)
        if config.name == "fax":
            # Case A: fax-service with zero requests
            rps_base = 0.0  # Always zero requests
            total_requests_base = 0  # No historical requests
            req_1d = 0.0  # No recent activity
            req_30d = 0.0  # No activity over 30 days
            req_6m = 0.0  # No historical data
        elif config.name == "price-discovery":
            # Case B: price-discovery-service with moderate consistent load
            rps_base = random.uniform(
                15, 25
            )  # Low utilization as mentioned in requirements
            total_requests_base = random.randint(
                50000, 80000
            )  # Historical moderate usage
            req_1d = 258.3
            req_30d = 341.0
            req_6m = 211.8
        elif config.name == "market-data":
            # High volume service
            rps_base = random.uniform(70, 80)
            total_requests_base = random.randint(100000, 200000)
            req_1d = 2533.1
            req_30d = 1501.0
            req_6m = 2212.4
        elif config.name == "position-management":
            rps_base = random.uniform(45, 55)
            total_requests_base = random.randint(30000, 70000)
            req_1d = 51.2
            req_30d = 67.0
            req_6m = 84.4
        elif config.name == "risk-management":
            rps_base = random.uniform(40, 50)
            total_requests_base = random.randint(40000, 80000)
            req_1d = 2368.3
            req_30d = 3010.0
            req_6m = 4010.1
        else:
            # Other services have normal patterns
            rps_base = random.uniform(10, 500)
            total_requests_base = random.randint(10000, 100000)
            req_1d = rps_base * 25.4  # Rough estimate from RPS
            req_30d = rps_base * 23.4  # 30 days worth
            req_6m = rps_base * 63

        return ServiceMetrics(
            cpu_usage=cpu_base,
            memory_usage=memory_base,
            memory_percentage=(memory_base / config.memory_range[1]) * 100,
            uptime_seconds=0,
            requests_per_second=rps_base,
            response_time_p50=random.uniform(1, 10),
            response_time_p95=random.uniform(10, 50),
            response_time_p99=random.uniform(50, 200),
            error_rate=random.uniform(0, 1.5),  # Keep under 2% to avoid error alerts
            queue_depth=random.randint(
                0, min(20, config.max_queue_depth // 2)
            ),  # Keep well under max
            active_connections=random.randint(active_conn_min, max_conn_half),
            total_requests=total_requests_base,
            total_errors=random.randint(0, int(total_requests_base * 0.01)),
            requests_1d=req_1d,
            requests_30d=req_30d,
            requests_6m=req_6m,
        )

    def update_metrics(self) -> ServiceMetrics:
        """Update service metrics with realistic variations."""
        if self.service.status != ServiceStatus.RUNNING:
            return self._base_metrics

        # Calculate uptime
        uptime = int((datetime.now() - self._start_time).total_seconds())

        # Add realistic variations to metrics
        if self.service.config.name == "fax":
            # Very small variation for fax service to keep it in 0-3% range
            # for workshop alert
            cpu_variation = random.uniform(
                -0.5, 0.5
            )  # Small variation around base 0.5-2.5%
        elif self.service.config.name == "price-discovery":
            # Moderate variation for price-discovery to keep it under 25%
            # threshold
            cpu_variation = random.uniform(
                -1, 1
            )  # Will stay under 25% for workshop alert
        else:
            # Other services: keep CPU in safe range (30-70%) to avoid any
            # alerts
            cpu_variation = random.uniform(-10, 10)  # Normal variation
        cpu_usage = max(0, min(100, self._base_metrics.cpu_usage + cpu_variation))

        # Keep memory variations safe - avoid high memory alerts
        if self.service.config.name in ["fax", "price-discovery"]:
            # Workshop services: keep memory usage low and stable
            memory_variation = random.randint(-10, 10)
        else:
            # Other services: moderate variation but keep under 80% to avoid
            # alerts
            memory_variation = random.randint(-30, 30)

        memory_usage = max(0, self._base_metrics.memory_usage + memory_variation)
        memory_percentage = min(
            80, (memory_usage / self.service.config.memory_range[1]) * 100
        )  # Cap at 80%

        # Simulate request patterns with workshop-specific scenarios
        hour = datetime.now().hour

        if self.service.config.name == "fax":
            # Case A: fax-service maintains zero requests
            rps = 0.0
        elif self.service.config.name == "price-discovery":
            # Case B: price-discovery-service has consistent moderate load
            base_rps = self._base_metrics.requests_per_second
            if 9 <= hour <= 17:  # Business hours - slight increase
                rps_multiplier = random.uniform(1.1, 1.3)
            else:
                rps_multiplier = random.uniform(0.8, 1.0)
            rps = base_rps * rps_multiplier
        else:
            # Normal services follow business hour patterns
            if 9 <= hour <= 17:  # Business hours
                rps_multiplier = random.uniform(1.5, 3.0)
            else:
                rps_multiplier = random.uniform(0.3, 0.8)
            rps = self._base_metrics.requests_per_second * rps_multiplier

        # Response times correlate with load
        load_factor = cpu_usage / 100.0
        p50 = self._base_metrics.response_time_p50 * (1 + load_factor)
        p95 = self._base_metrics.response_time_p95 * (1 + load_factor * 1.5)
        p99 = self._base_metrics.response_time_p99 * (1 + load_factor * 2)

        # Error rate increases with high load but stays under alert thresholds
        error_rate = self._base_metrics.error_rate
        if cpu_usage > 80:
            error_rate = min(
                1.8, error_rate * random.uniform(1.2, 1.5)
            )  # Cap under 2% threshold
        elif cpu_usage > 60:
            error_rate = min(
                1.5, error_rate * random.uniform(1.0, 1.2)
            )  # Keep well under 2%
        else:
            error_rate = min(1.0, error_rate)  # Very low error rate for normal load

        # Queue depth increases with high load but stays well under max
        base_queue_factor = max(
            0.3, (1 + load_factor) * 0.5
        )  # More conservative scaling
        queue_depth = int(self._base_metrics.queue_depth * base_queue_factor)
        queue_depth = min(
            queue_depth, int(self.service.config.max_queue_depth * 0.7)
        )  # Stay under 70% of max

        # Active connections vary
        conn_variation = random.randint(-10, 20)
        active_connections = max(
            0,
            min(
                self.service.config.max_connections,
                self._base_metrics.active_connections + conn_variation,
            ),
        )

        # Update totals
        requests_increment = int(rps * 5)  # Assuming 5-second update interval
        total_requests = self._base_metrics.total_requests + requests_increment

        errors_increment = int(requests_increment * (error_rate / 100))
        total_errors = self._base_metrics.total_errors + errors_increment

        updated_metrics = ServiceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            memory_percentage=memory_percentage,
            uptime_seconds=uptime,
            requests_per_second=rps,
            response_time_p50=p50,
            response_time_p95=p95,
            response_time_p99=p99,
            error_rate=error_rate,
            queue_depth=queue_depth,
            active_connections=active_connections,
            total_requests=total_requests,
            total_errors=total_errors,
            # Preserve historical request data
            requests_1d=self._base_metrics.requests_1d,
            requests_30d=self._base_metrics.requests_30d,
            requests_6m=self._base_metrics.requests_6m,
        )

        # Update base metrics for next iteration
        self._base_metrics = updated_metrics
        return updated_metrics


class ServiceManager:
    """Manages all services in the trading venue simulation."""

    def __init__(self, deployment_file: Optional[str] = None):
        self.services: Dict[str, Service] = {}
        self.simulators: Dict[str, ServiceSimulator] = {}
        self.cluster_nodes: List[ClusterNode] = []
        self.deployment_loader = DeploymentLoader(deployment_file)
        self._initialize_from_deployment()

    def _initialize_from_deployment(self) -> None:
        """Initialize cluster and services from deployment configuration."""
        # Load cluster nodes from deployment
        self.cluster_nodes = self.deployment_loader.get_cluster_nodes()

        # Update each node with the services deployed on it
        deployment_config = self.deployment_loader.load_config()
        for service_data in deployment_config.services:
            service_name = service_data.get("name", "")
            machines = service_data.get("deployment", {}).get("machines", [])

            for machine in machines:
                # Convert machine hostname to node_id
                if machine.startswith("trading-"):
                    node_id = machine.replace("trading-", "")
                else:
                    node_id = machine

                # Find the corresponding cluster node and add service
                for node in self.cluster_nodes:
                    if node.node_id == node_id:
                        service_short_name = service_name.replace("-service", "")
                        node.services.append(service_short_name)
                        break

        # Load service configurations from deployment
        service_configs = self.deployment_loader.get_service_configs()

        for config in service_configs:
            service = Service(
                config=config,
                status=ServiceStatus.RUNNING,
                start_time=datetime.now()
                - timedelta(
                    seconds=random.randint(3600, 86400)  # Random uptime 1-24 hours
                ),
                pid=random.randint(1000, 9999),
                version=self._get_service_version(config.name),
                description=config.description,
            )

            self.services[config.name] = service
            self.simulators[config.name] = ServiceSimulator(service)

            # Initialize with special metrics for workshop scenarios
            self._initialize_workshop_metrics(service)

    def _get_service_version(self, service_name: str) -> str:
        """Get service version from deployment configuration."""
        deployment_config = self.deployment_loader.load_config()

        # Find the service in deployment config and return its version
        for service_data in deployment_config.services:
            deployed_name = service_data.get("name", "")
            if deployed_name.replace("-service", "") == service_name:
                return service_data.get("version", "1.0.0")

        return "1.0.0"  # Default version

    def _check_market_data_optimization(self) -> bool:
        """
        Check if get_market_data.py has been optimized by analyzing the code.
        Returns True if optimized (bulk API), False if inefficient (individual calls).
        """
        import os

        market_data_file = os.path.join(os.path.dirname(__file__), "get_market_data.py")

        try:
            with open(market_data_file, "r") as f:
                content = f.read()

            # Check if the inefficient loop is commented out or removed
            # Look for the for loop pattern that makes individual API calls
            inefficient_patterns = [
                "for ticker in tickers:",
                "api_client.get_equity_spot(ticker)",
            ]

            # Check if bulk API is being used (uncommented)
            optimized_patterns = [
                "api_client.get_bulk_market_data(",
                "api_client.get_bulk_market_data(tickers)",
            ]

            # Count how many inefficient patterns are active (not commented)
            active_inefficient = 0
            for pattern in inefficient_patterns:
                # Find all occurrences of the pattern
                lines = content.split("\n")
                for line in lines:
                    if pattern in line:
                        # Check if the line is not commented out
                        stripped = line.strip()
                        if not stripped.startswith("#") and not stripped.startswith(
                            "//"
                        ):
                            active_inefficient += 1
                            break

            # Count how many optimized patterns are active (not commented)
            active_optimized = 0
            for pattern in optimized_patterns:
                lines = content.split("\n")
                for line in lines:
                    if pattern in line:
                        # Check if the line is not commented out
                        stripped = line.strip()
                        if not stripped.startswith("#") and not stripped.startswith(
                            "//"
                        ):
                            active_optimized += 1
                            break

            # If optimized patterns are active and inefficient patterns are
            # not, it's optimized
            return active_optimized >= 1 and active_inefficient <= 1

        except Exception:
            # If we can't read the file, assume it's not optimized
            return False

    def _initialize_workshop_metrics(self, service: Service) -> None:
        """Initialize special metrics for workshop scenarios."""
        # Check if Exercise 1 is completed (fax-service removed)
        fax_service_exists = "fax" in self.services

        if service.config.name == "fax":
            # Case A: Almost zero utilization service - ensure CPU stays under
            # 3% threshold
            service.metrics = ServiceMetrics(
                cpu_usage=random.uniform(
                    0.5, 2.5
                ),  # Stays under 3% threshold for alert
                memory_usage=64,
                memory_percentage=25.0,
                uptime_seconds=random.randint(3600, 86400),
                requests_per_second=0.0,  # No requests!
                response_time_p50=0.0,
                response_time_p95=0.0,
                response_time_p99=0.0,
                error_rate=0.0,
                queue_depth=0,
                active_connections=0,
                total_requests=0,
                total_errors=0,
                requests_1d=0.0,  # No requests in last day
                requests_30d=0.0,  # No requests in 30 days
                requests_6m=0.0,  # No requests in 6 months
            )
        elif service.config.name == "position-management":
            # Case B: Low utilization but has requests (overprovisioned)
            service.metrics = ServiceMetrics(
                cpu_usage=12.0,
                memory_usage=180,
                memory_percentage=35.0,
                uptime_seconds=random.randint(3600, 86400),
                requests_per_second=25.0,  # Has requests but low CPU
                response_time_p50=2.0,
                response_time_p95=8.0,
                response_time_p99=15.0,
                error_rate=0.1,
                queue_depth=2,
                active_connections=45,
                total_requests=random.randint(50000, 100000),
                total_errors=random.randint(10, 50),
            )
        elif service.config.name == "market-data" and not fax_service_exists:
            # Checkpoint 3: High latency service (only show after Exercise 1 completion)
            # Analyze code to determine if optimized without running it

            is_optimized = self._check_market_data_optimization()

            if is_optimized:
                # Fast optimized version (0.1 seconds = 100ms)
                actual_response_time = 100.0
            else:
                # Slow inefficient version (20 seconds = 20000ms)
                actual_response_time = 20000.0

            # Use response times with some variation
            p50_time = actual_response_time * random.uniform(0.9, 1.1)
            p95_time = actual_response_time * random.uniform(1.2, 1.5)
            p99_time = actual_response_time * random.uniform(1.5, 2.0)

            service.metrics = ServiceMetrics(
                cpu_usage=25.0,
                memory_usage=450,
                memory_percentage=65.0,
                uptime_seconds=random.randint(3600, 86400),
                requests_per_second=15.0,
                response_time_p50=p50_time,
                response_time_p95=p95_time,
                response_time_p99=p99_time,
                error_rate=0.5,
                queue_depth=50,
                active_connections=25,
                total_requests=random.randint(30000, 60000),
                total_errors=random.randint(150, 300),
                requests_1d=2533.1,
                requests_30d=0.0,
                requests_6m=188.4,
            )
        else:
            # Normal services - use simulator metrics
            simulator = self.simulators.get(service.config.name)
            if simulator:
                service.metrics = simulator.update_metrics()

    def get_service(self, name: str) -> Optional[Service]:
        """Get a service by name."""
        return self.services.get(name)

    def get_all_services(self) -> List[Service]:
        """Get all services."""
        return list(self.services.values())

    def get_running_services(self) -> List[Service]:
        """Get all running services."""
        return [s for s in self.services.values() if s.status == ServiceStatus.RUNNING]

    def start_service(self, name: str) -> bool:
        """Start a service."""
        service = self.services.get(name)
        if not service:
            return False

        if service.status == ServiceStatus.RUNNING:
            return True

        service.status = ServiceStatus.STARTING
        time.sleep(0.1)  # Simulate startup time
        service.status = ServiceStatus.RUNNING
        service.start_time = datetime.now()
        service.pid = random.randint(1000, 9999)

        # Reset simulator
        if name in self.simulators:
            self.simulators[name] = ServiceSimulator(service)
            service.metrics = self.simulators[name].update_metrics()

        return True

    def stop_service(self, name: str) -> bool:
        """Stop a service."""
        service = self.services.get(name)
        if not service:
            return False

        if service.status == ServiceStatus.STOPPED:
            return True

        service.status = ServiceStatus.STOPPING
        time.sleep(0.1)  # Simulate shutdown time
        service.status = ServiceStatus.STOPPED
        service.start_time = None
        service.pid = None
        service.metrics = None

        return True

    def update_all_metrics(self) -> None:
        """Update metrics for all running services."""
        for name, service in self.services.items():
            if service.status == ServiceStatus.RUNNING and name in self.simulators:
                service.metrics = self.simulators[name].update_metrics()

    def get_system_overview(self) -> SystemOverview:
        """Get overall system status."""
        services = list(self.services.values())

        total_services = len(services)
        running_services = len(
            [s for s in services if s.status == ServiceStatus.RUNNING]
        )
        stopped_services = len(
            [s for s in services if s.status == ServiceStatus.STOPPED]
        )
        error_services = len([s for s in services if s.status == ServiceStatus.ERROR])

        # Aggregate metrics from running services
        total_cpu = 0.0
        total_memory = 0.0
        total_rps = 0.0
        total_response_times = []
        total_connections = 0

        running_services_list = [
            s for s in services if s.status == ServiceStatus.RUNNING and s.metrics
        ]

        for service in running_services_list:
            if service.metrics:
                total_cpu += service.metrics.cpu_usage
                total_memory += service.metrics.memory_usage
                total_rps += service.metrics.requests_per_second
                total_response_times.append(service.metrics.response_time_p50)
                total_connections += service.metrics.active_connections

        avg_response_time = (
            sum(total_response_times) / len(total_response_times)
            if total_response_times
            else 0.0
        )

        # Generate alerts for services with issues
        alerts = self._generate_alerts(services)

        return SystemOverview(
            total_services=total_services,
            running_services=running_services,
            stopped_services=stopped_services,
            error_services=error_services,
            total_cpu_usage=total_cpu,
            total_memory_usage=total_memory,
            total_requests_per_second=total_rps,
            average_response_time=avg_response_time,
            total_active_connections=total_connections,
            cluster_nodes=self.cluster_nodes,  # Include cluster information
            alerts=alerts,
        )

    def _generate_alerts(self, services: List[Service]) -> List[Alert]:
        """Generate alerts for services with issues based on workshop progression."""
        alerts = []

        # Workshop-specific progressive alerts based on exercise completion
        workshop_alerts = self._generate_workshop_alerts(services)
        alerts.extend(workshop_alerts)

        return alerts

    def _generate_workshop_alerts(self, services: List[Service]) -> List[Alert]:
        """Generate workshop-specific alerts based on exercise progression."""
        alerts = []

        # Determine current workshop state
        fax_present = any(s.config.name == "fax" for s in services)
        market_data_service = next(
            (s for s in services if s.config.name == "market-data"), None
        )

        # Check if market-data service has been optimized (efficient
        # implementation used)
        market_data_optimized = self._check_market_data_optimization()

        # Checkpoint 1: Show fax-service alert only if fax is present
        if fax_present:
            fax_service = next(s for s in services if s.config.name == "fax")
            if fax_service.metrics and fax_service.metrics.cpu_usage < 3.0:
                alerts.append(
                    Alert(
                        service_name="fax",
                        level=AlertLevel.WARNING,
                        message="Low utilization on large machine - investigate service necessity\n" +
                                "           → Run: `python3 workshop.py historical fax-service`",
                        metric_name="cpu_usage",
                        current_value=fax_service.metrics.cpu_usage,
                        threshold=3.0,
                    )
                )

        # Checkpoint 2: Show market-data alert only after fax is removed
        elif not fax_present and not market_data_optimized:
            if market_data_service and market_data_service.metrics:
                # Show general performance alert
                alerts.append(
                    Alert(
                        service_name="market-data",
                        level=AlertLevel.WARNING,
                        message="Service showing performance issues - investigate code inefficiencies in the function getMarketData(api_client) in the file get_market_data.py",
                        metric_name="response_time",
                        current_value=market_data_service.metrics.response_time_p95,
                        threshold=1000.0,
                    )
                )

        return alerts

    def get_cluster_nodes(self) -> List[ClusterNode]:
        """Get all cluster nodes."""
        return self.cluster_nodes.copy()

    def get_services_on_node(self, node_id: str) -> List[Service]:
        """Get all services running on a specific node."""
        node = next((n for n in self.cluster_nodes if n.node_id == node_id), None)
        if not node:
            return []

        services = []
        for service_name in node.services:
            service = self.services.get(service_name)
            if service:
                services.append(service)
        return services


# Copyright 2025 Bloomberg Finance L.P.
