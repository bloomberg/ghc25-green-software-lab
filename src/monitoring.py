"""Monitoring and real-time display functionality."""

import time
from datetime import datetime
from typing import Dict, List, Optional

from .models import Service, SystemOverview
from .services import ServiceManager


class Monitor:
    """Real-time monitoring and display manager."""

    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager
        self.history: Dict[str, List[Dict]] = {}
        self.max_history = 100

    def start_monitoring(
        self, interval: int = 5, services: Optional[List[str]] = None
    ) -> None:
        """Start real-time monitoring with specified interval."""
        print(f"Starting monitoring (refresh every {interval}s)...")
        print("Press Ctrl+C to stop monitoring\n")

        try:
            while True:
                self.service_manager.update_all_metrics()

                if services:
                    service_list = [
                        self.service_manager.get_service(name) for name in services
                    ]
                    service_list = [s for s in service_list if s is not None]
                else:
                    service_list = self.service_manager.get_all_services()

                self._display_services(service_list)
                self._update_history(service_list)

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")

    def get_current_status(self) -> SystemOverview:
        """Get current system status."""
        self.service_manager.update_all_metrics()
        return self.service_manager.get_system_overview()

    def get_service_status(self, name: str) -> Optional[Service]:
        """Get status of a specific service."""
        self.service_manager.update_all_metrics()
        return self.service_manager.get_service(name)

    def _display_services(self, services: List[Service]) -> None:
        """Display services in a formatted table."""
        # Clear screen (works on most terminals)
        print("\033[2J\033[H")

        print(
            f"Workshop Service Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 80)

        # Header
        print(
            f"{'Service':<20} {'Status':<12} {'CPU%':<8} {'Memory':<12} {'Req/Sec':<8} {'Uptime':<12}"
        )
        print("-" * 80)

        # Service rows
        for service in services:
            memory_display = (
                f"{service.metrics.memory_usage:.0f}MB" if service.metrics else "N/A"
            )
            rps_display = (
                f"{service.metrics.requests_per_second:.1f}" if service.metrics else "0"
            )
            uptime_display = service.get_uptime_display()
            cpu_display = f"{service.metrics.cpu_usage:.1f}" if service.metrics else "0"

            print(
                f"{service.config.name:<20} "
                f"{service.status.value:<12} "
                f"{cpu_display:<8} "
                f"{memory_display:<12} "
                f"{rps_display:<8} "
                f"{uptime_display:<12}"
            )

        # Summary
        overview = self.service_manager.get_system_overview()
        print("-" * 80)
        print(
            f"System Health: {overview.health_percentage:.1f}% | "
            f"Running: {overview.running_services}/{overview.total_services} | "
            f"Total Requests/Sec: {overview.total_requests_per_second:.1f} | "
            f"Avg Response: {overview.average_response_time:.1f}ms"
        )

        # Alerts
        if overview.alerts:
            print("\nAlerts:")
            for alert in overview.alerts[:5]:  # Show only first 5 alerts
                print(
                    f"  [{alert.level.value.upper()}] {alert.service_name}: {alert.message}"
                )

        print()

    def _update_history(self, services: List[Service]) -> None:
        """Update historical metrics."""
        timestamp = datetime.now()

        for service in services:
            if service.metrics:
                if service.config.name not in self.history:
                    self.history[service.config.name] = []

                history_point = {
                    "timestamp": timestamp,
                    "cpu_usage": service.metrics.cpu_usage,
                    "memory_usage": service.metrics.memory_usage,
                    "requests_per_second": service.metrics.requests_per_second,
                    "response_time_p95": service.metrics.response_time_p95,
                    "error_rate": service.metrics.error_rate,
                }

                self.history[service.config.name].append(history_point)

                # Keep only the last N points
                if len(self.history[service.config.name]) > self.max_history:
                    self.history[service.config.name] = self.history[
                        service.config.name
                    ][-self.max_history :]

    def get_service_history(self, service_name: str, points: int = 10) -> List[Dict]:
        """Get recent history for a service."""
        if service_name not in self.history:
            return []

        return self.history[service_name][-points:]

    def display_service_table(self, services: Optional[List[Service]] = None) -> None:
        """Display services in a static table format."""
        if services is None:
            self.service_manager.update_all_metrics()
            services = self.service_manager.get_all_services()

        print(
            f"Workshop Service Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 100)

        header = (
            f"{'Service':<18} {'Status':<12} {'CPU%':<8} {'Memory':<12} "
            f"{'Req/Sec':<8} {'P95ms':<8} {'Err%':<6} {'Uptime':<12}"
        )
        print(header)
        print("-" * 100)

        # Service rows
        for service in sorted(services, key=lambda x: x.config.name):
            if service.metrics:
                memory_mb = f"{service.metrics.memory_usage:.0f}MB"
                rps = f"{service.metrics.requests_per_second:.1f}"
                p95 = f"{service.metrics.response_time_p95:.1f}"
                err_rate = f"{service.metrics.error_rate:.1f}"
                cpu = f"{service.metrics.cpu_usage:.1f}"
            else:
                memory_mb = "N/A"
                rps = "0"
                p95 = "N/A"
                err_rate = "N/A"
                cpu = "0"

            uptime = service.get_uptime_display()

            row = (
                f"{service.config.name:<18} {service.status.value:<12} {cpu:<8} "
                f"{memory_mb:<12} {rps:<8} {p95:<8} {err_rate:<6} {uptime:<12}"
            )
            print(row)

        overview = self.service_manager.get_system_overview()
        print("-" * 100)
        print(
            f"Summary: {overview.running_services}/{overview.total_services} services running | "
            f"Total Requests/Sec: {overview.total_requests_per_second:.1f} | "
            f"System Health: {overview.health_percentage:.1f}%"
        )

        if overview.alerts:
            print(f"\nActive Alerts ({len(overview.alerts)}):")
            for alert in overview.alerts:
                print(
                    f"  [{alert.level.value.upper()}] {alert.service_name}: {alert.message}"
                )

        self._display_workshop_recommendations(services, overview)

    def display_workshop_dashboard(
        self, services: Optional[List[Service]] = None
    ) -> None:
        """Display services in workshop format with deployment information."""
        if services is None:
            self.service_manager.update_all_metrics()
            services = self.service_manager.get_all_services()

        print("=" * 108)

        header = (
            f"{'Service':<19} {'Status':<12} {'CPU%':<8} {'Memory':<12} "
            f"{'Req/1D':<8} {'Req/30D':<8} {'Req/6M':<8} {'Deployment':<25}"
        )
        print(header)
        print("-" * 108)

        # Get deployment configuration for machine size mapping
        deployment_loader = self.service_manager.deployment_loader
        cluster_nodes = deployment_loader.get_cluster_nodes()
        node_size_map = {
            node.node_id: self._get_machine_size_name(node.cpu_cores)
            for node in cluster_nodes
        }

        # Service rows
        for service in sorted(services, key=lambda x: x.config.name):
            # Service name (remove '-service' suffix for display)
            display_name = service.config.name.replace("-service", "")

            if service.metrics:
                cpu = f"{service.metrics.cpu_usage:.1f}"
                memory_mb = f"{service.metrics.memory_usage:.0f}MB"
                # Use historical request data from metrics
                req_1d = (
                    f"{service.metrics.requests_1d:.1f}"
                    if service.metrics.requests_1d is not None
                    else "0.0"
                )
                req_30d = (
                    f"{service.metrics.requests_30d:.1f}"
                    if service.metrics.requests_30d is not None
                    else ""
                )
                req_6m = (
                    f"{service.metrics.requests_6m:.1f}"
                    if service.metrics.requests_6m is not None
                    else "0.0"
                )
            else:
                cpu = "0.0"
                memory_mb = "0MB"
                req_1d = "0.0"
                req_30d = ""
                req_6m = "0.0"

            # Build deployment string (node:size format)
            deployment_info = []
            for node_id in service.config.cluster_nodes:
                size = node_size_map.get(node_id, "unknown")
                deployment_info.append(f"{node_id}:{size.capitalize()}")

            deployment = ", ".join(deployment_info) if deployment_info else "none"

            row = (
                f"{display_name:<19} {service.status.value:<12} {cpu:<8} {memory_mb:<12} "
                f"{req_1d:<8} {req_30d:<8} {req_6m:<8} {deployment:<25}"
            )
            print(row)

        print("-" * 108)

        # Get system overview for alerts
        overview = self.service_manager.get_system_overview()

        # Display recommendations based on active alerts
        self._display_workshop_recommendations(services, overview)

    def _get_machine_size_name(self, cpu_cores: int) -> str:
        """Get machine size name from CPU cores."""
        if cpu_cores == 2:
            return "X-Small"
        elif cpu_cores == 4:
            return "Small"
        elif cpu_cores == 16:
            return "Large"
        else:
            return "Medium"

    def display_service_details(self, service_name: str) -> None:
        """Display detailed information about a specific service."""
        self.service_manager.update_all_metrics()
        service = self.service_manager.get_service(service_name)

        if not service:
            print(f"Service '{service_name}' not found.")
            return

        print(f"Service Details: {service.config.name}")
        print("=" * 50)
        print(f"Type: {service.config.service_type.value}")
        print(f"Description: {service.description}")
        print(f"Status: {service.status.value}")
        print(f"Port: {service.config.port}")
        print(f"PID: {service.pid or 'N/A'}")
        print(f"Version: {service.version}")

        if service.metrics:
            print("\nCurrent Metrics:")
            print(f"  CPU Usage: {service.metrics.cpu_usage:.2f}%")
            print(
                f"  Memory: {service.metrics.memory_usage:.0f}MB "
                f"({service.metrics.memory_percentage:.1f}%)"
            )
            print(f"  Uptime: {service.get_uptime_display()}")
            print(f"  Requests/sec: {service.metrics.requests_per_second:.2f}")
            print(
                f"  Response Times: P50={service.metrics.response_time_p50:.1f}ms, "
                f"P95={service.metrics.response_time_p95:.1f}ms, "
                f"P99={service.metrics.response_time_p99:.1f}ms"
            )
            print(f"  Error Rate: {service.metrics.error_rate:.2f}%")
            print(f"  Queue Depth: {service.metrics.queue_depth}")
            print(f"  Active Connections: {service.metrics.active_connections}")
            print(f"  Total Requests: {service.metrics.total_requests:,}")
            print(f"  Total Errors: {service.metrics.total_errors:,}")

        print("\nConfiguration:")
        print(f"  Max Connections: {service.config.max_connections}")
        print(f"  Max Queue Depth: {service.config.max_queue_depth}")
        print(
            f"  CPU Range: {service.config.cpu_range[0]:.1f}% - "
            f"{service.config.cpu_range[1]:.1f}%"
        )
        print(
            f"  Memory Range: {service.config.memory_range[0]}MB - "
            f"{service.config.memory_range[1]}MB"
        )

        if service.config.dependencies:
            print(f"  Dependencies: {', '.join(service.config.dependencies)}")

        print(f"\nHealth Status: {'Healthy' if service.is_healthy() else 'Unhealthy'}")

        # Show recent history if available
        history = self.get_service_history(service_name, 5)
        if history:
            print("\nRecent History (last 5 points):")
            for i, point in enumerate(history):
                print(
                    f"  {i + 1}. {point['timestamp'].strftime('%H:%M:%S')} - "
                    f"CPU: {point['cpu_usage']:.1f}%, "
                    f"RPS: {point['requests_per_second']:.1f}"
                )

    def display_metrics_summary(self) -> None:
        """Display a summary of key metrics across all services."""
        self.service_manager.update_all_metrics()
        overview = self.service_manager.get_system_overview()
        services = self.service_manager.get_running_services()

        print(f"Metrics Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        print("System Overview:")
        print(f"  Total Services: {overview.total_services}")
        print(f"  Running: {overview.running_services}")
        print(f"  Stopped: {overview.stopped_services}")
        print(f"  Error State: {overview.error_services}")
        print(f"  Health: {overview.health_percentage:.1f}%")

        print("\nAggregated Metrics:")
        print(f"  Total CPU Usage: {overview.total_cpu_usage:.1f}%")
        print(f"  Total Memory: {overview.total_memory_usage:.0f}MB")
        print(f"  Total Requests/Sec: {overview.total_requests_per_second:.1f}")
        print(f"  Average Response Time: {overview.average_response_time:.1f}ms")
        print(f"  Total Connections: {overview.total_active_connections}")

        if services:
            high_cpu_services = [
                s for s in services if s.metrics and s.metrics.cpu_usage > 70
            ]
            high_error_services = [
                s for s in services if s.metrics and s.metrics.error_rate > 1
            ]

            if high_cpu_services:
                print("\nHigh CPU Usage Services:")
                for service in high_cpu_services:
                    print(
                        f"  {service.config.name}: " f"{service.metrics.cpu_usage:.1f}%"
                    )

            if high_error_services:
                print("\nServices with Elevated Error Rates:")
                for service in high_error_services:
                    print(
                        f"  {service.config.name}: "
                        f"{service.metrics.error_rate:.2f}%"
                    )

        if overview.alerts:
            print(f"\nActive Alerts ({len(overview.alerts)}):")
            for alert in overview.alerts:
                print(
                    f"  [{alert.level.value.upper()}] "
                    f"{alert.service_name}: {alert.message}"
                )

    def _display_workshop_recommendations(
        self, services: List[Service], overview
    ) -> None:
        """Display workshop activity recommendations based on current system state."""
        from pathlib import Path

        # Check if Exercise 1 has been completed (fax-service removed)
        fax_service_exists = any(s.config.name == "fax-service" for s in services)

        # Check if Checkpoint 2 has been completed (market-data-service
        # optimized)
        checkpoint_2_completed = False
        market_data_file = Path("src/get_market_data.py")
        if market_data_file.exists():
            content = market_data_file.read_text()
            if "bulk_api" in content or "batch" in content.lower():
                checkpoint_2_completed = True

        # Only show recommendations if there are active alerts
        if overview.alerts:
            print("\n🚨 WORKSHOP RECOMMENDATIONS")
            print("=" * 28)
            for alert in overview.alerts:
                service_name = alert.service_name
                if "error" in alert.message.lower():
                    print(
                        f"   • {service_name}-service: Elevated error rate - review service health"
                    )
                elif "cpu" in alert.message.lower() and "high" in alert.message.lower():
                    print(
                        f"   • {service_name}-service: High CPU usage - analyze workload patterns"
                    )
                else:
                    # Use the actual alert message for other cases (including
                    # fax service low utilization)
                    print(f"   • {service_name}-service: {alert.message}")

            # Checkpoint 2 recommendations (only show after Checkpoint 1
            # completion)
            if not fax_service_exists and not checkpoint_2_completed:
                market_data_service = next(
                    (s for s in services if s.config.name == "market-data-service"),
                    None,
                )
                if market_data_service and market_data_service.metrics:
                    # Simulate high latency for market-data-service after
                    # Checkpoint 1
                    if (
                        market_data_service.metrics.response_time_p95 > 1000
                    ):  # > 1 second
                        print("\n⚡ PERFORMANCE ALERT")
                        print("=" * 50)
                        print(
                            "   • market-data-service: Excessive response times detected"
                        )
                        print("   • Average response time: 5+ minutes per request")
                        print(
                            "   • 💡 RECOMMENDATION: Review latency dashboard with 'python3 workshop.py latency'"
                        )
                        print(
                            "   • 🔍 INVESTIGATION: Check src/get_market_data.py for code inefficiencies"
                        )

            # Checkpoint 3 recommendations (only show after Checkpoints 1 and 2
            # completion)
            if not fax_service_exists and checkpoint_2_completed:
                print("\n🌱 SUSTAINABILITY ALERT")
                print("=" * 50)
                print(
                    "   • Risk calculation jobs: Resource contention and high carbon footprint detected"
                )
                print(
                    "   • All 5 jobs scheduled simultaneously at 18:00 (peak carbon hours)"
                )
                print(
                    "   • 💡 RECOMMENDATION: Review job scheduler with 'python3 workshop.py scheduler'"
                )
                print(
                    "   • 🔍 INVESTIGATION: Analyze carbon intensity patterns with 'python3 workshop.py carbon'"
                )
                print(
                    "   • 🎯 OPTIMIZATION: Reschedule jobs to low-carbon periods (2-6 AM)"
                )

            print()


# Copyright 2025 Bloomberg Finance L.P.
