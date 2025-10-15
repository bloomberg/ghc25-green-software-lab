"""Deployment configuration loader for the workshop service tool."""

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import ClusterNode, ServiceConfig, ServiceType
from .yaml_utils import SimpleYAMLParser


class DeploymentConfig:
    """Represents deployment configuration from deployment.yaml."""

    def __init__(self):
        self.metadata: Dict[str, Any] = {}
        self.cluster: Dict[str, Any] = {}
        self.machines: List[Dict[str, Any]] = []
        self.services: List[Dict[str, Any]] = []
        self.monitoring: Dict[str, Any] = {}

    @classmethod
    def from_yaml(cls, file_path: str) -> "DeploymentConfig":
        """Load deployment configuration from YAML file."""
        config = cls()

        try:
            # Parse the YAML file using our simple parser
            yaml_data = SimpleYAMLParser.parse_file(file_path)

            # Extract metadata
            config.metadata = yaml_data.get("metadata", {})

            # Extract cluster info
            config.cluster = yaml_data.get("cluster", {})

            # Extract machines
            config.machines = yaml_data.get("machines", [])

            # Extract services
            config.services = yaml_data.get("services", [])

            # Extract monitoring
            config.monitoring = yaml_data.get("monitoring", {})

        except Exception as e:
            print(f"Warning: Could not parse YAML file {file_path}: {e}")
            print("Falling back to default configuration...")

            # Fallback to hardcoded configuration
            config.metadata = {
                "name": "trading-services-cluster",
                "description": "Financial Trading Services Workshop Deployment",
                "version": "1.0.0",
            }

            config.cluster = {"name": "trading-cluster", "size": 5}

            config.machines = [
                {"hostname": "node1", "size": "small"},
                {"hostname": "node2", "size": "large"},
                {"hostname": "node3", "size": "large"},
                {"hostname": "node4", "size": "small"},
                {"hostname": "node5", "size": "small"},
            ]

            config.services = [
                {
                    "name": "price-discovery-service",
                    "version": "1.8.2",
                    "description": "Market price discovery and calculation engine",
                    "deployment": {"machines": ["node2"]},
                },
                {
                    "name": "position-management-service",
                    "version": "3.0.1",
                    "description": "Portfolio position tracking and management",
                    "deployment": {"machines": ["node1", "node3", "node4", "node5"]},
                },
                {
                    "name": "market-data-service",
                    "version": "2.5.0",
                    "description": "Real-time market data ingestion and processing",
                    "deployment": {"machines": ["node3", "node4", "node5"]},
                },
                {
                    "name": "risk-management-service",
                    "version": "1.9.7",
                    "description": "Risk calculation and monitoring system",
                    "deployment": {"machines": ["node4", "node5"]},
                },
            ]

            config.monitoring = {
                "enabled": True,
                "metrics_port": 9090,
                "log_level": "INFO",
                "retention_days": 30,
            }

        return config


class DeploymentLoader:
    """Loads and converts deployment configuration to workshop models."""

    def __init__(self, deployment_file: Optional[str] = None):
        if deployment_file is None:
            # Default to the deployment.yaml in the configuration_files
            # directory
            base_path = (
                Path(__file__).parent / "configuration_files" / "deployment.yaml"
            )
            deployment_file = str(base_path)

        self.deployment_file = deployment_file
        self._config: Optional[DeploymentConfig] = None

    def load_config(self) -> DeploymentConfig:
        """Load the deployment configuration."""
        if self._config is None:
            self._config = DeploymentConfig.from_yaml(self.deployment_file)
        return self._config

    def get_cluster_nodes(self) -> List[ClusterNode]:
        """Convert deployment machines to ClusterNode objects."""
        config = self.load_config()
        nodes = []

        for i, machine in enumerate(config.machines):
            hostname = machine.get("hostname", f"node-{i + 1:02d}")

            # Extract node ID from hostname (e.g., node1 -> node-01)
            node_id = hostname.replace("trading-", "")

            # Determine resources based on machine size
            size = machine.get("size", "medium")
            if size == "small":
                cpu_cores, memory_gb = 4, 16
            elif size == "large":
                cpu_cores, memory_gb = 16, 64
            elif size == "x-small":
                cpu_cores, memory_gb = 2, 8
            else:  # medium
                cpu_cores, memory_gb = 8, 32

            node = ClusterNode(
                node_id=node_id,
                hostname=hostname,
                cpu_cores=cpu_cores,
                memory_gb=memory_gb,
                is_active=True,
            )
            nodes.append(node)

        return nodes

    def get_service_configs(self) -> List[ServiceConfig]:
        """Convert deployment services to ServiceConfig objects."""
        config = self.load_config()
        service_configs = []

        # Mapping from service names to ServiceType enums
        service_type_mapping = {
            "fax-service": ServiceType.FAX,
            "price-discovery-service": ServiceType.PRICE_DISCOVERY,
            "position-management-service": ServiceType.POSITION_MANAGEMENT,
            "market-data-service": ServiceType.MARKET_DATA,
            "risk-management-service": ServiceType.RISK_MANAGEMENT,
            "order-matching-service": ServiceType.ORDER_MATCHING,
            "settlement-service": ServiceType.SETTLEMENT,
            "authentication-service": ServiceType.AUTHENTICATION,
        }

        # Port mapping for services
        port_mapping = {
            "fax-service": 8006,
            "price-discovery-service": 8008,
            "position-management-service": 8007,
            "market-data-service": 8002,
            "risk-management-service": 8003,
            "order-matching-service": 8001,
            "settlement-service": 8004,
            "authentication-service": 8005,
        }

        for service_data in config.services:
            name = service_data.get("name", "")
            description = service_data.get("description", "")
            deployment = service_data.get("deployment", {})
            machines = deployment.get("machines", [])

            # Convert machine hostnames to node IDs
            cluster_nodes = []
            for machine in machines:
                if machine.startswith("trading-"):
                    node_id = machine.replace("trading-", "")
                    cluster_nodes.append(node_id)
                else:
                    cluster_nodes.append(machine)

            # Get service type from mapping
            service_type = service_type_mapping.get(name, ServiceType.FAX)

            # Get port from mapping
            port = port_mapping.get(name, 8000)

            # Set resource ranges based on service type and deployment scenario
            cpu_range, memory_range, max_connections = self._get_service_resources(
                name, len(machines)
            )

            service_config = ServiceConfig(
                name=name.replace(
                    "-service", ""
                ),  # Remove -service suffix for consistency
                service_type=service_type,
                port=port,
                cpu_range=cpu_range,
                memory_range=memory_range,
                max_connections=max_connections,
                description=description,
                cluster_nodes=cluster_nodes,
                preferred_node=cluster_nodes[0] if cluster_nodes else None,
            )

            service_configs.append(service_config)

        return service_configs

    def _get_service_resources(self, service_name: str, machine_count: int) -> tuple:
        """Determine resource ranges based on service name and deployment pattern."""

        # Workshop scenario configurations
        if service_name == "fax-service":
            # Case A: Very low utilization service (workshop scenario)
            # Running on oversized 'large' machine with minimal usage
            return (0.5, 2.0), (64, 128), 50
        elif service_name == "price-discovery-service":
            # Case B: Overprovisioned service with suboptimal resource allocation
            # Running on 'large' machine but low utilization (5-7% as per
            # requirements)
            return (5, 9), (1024, 2048), 300
        elif service_name == "position-management-service":
            # Normal distributed service for comparison
            return (30, 60), (256, 512), 800
        elif service_name == "market-data-service":
            # High-performance service
            return (40, 80), (512, 1024), 5000
        elif service_name == "risk-management-service":
            # Medium performance service
            return (25, 55), (256, 512), 500
        else:
            # Default configuration
            return (10, 50), (256, 1024), 1000


class DeploymentManager:
    """Manages deployment configuration changes for workshop exercises."""

    def __init__(self, deployment_file: Optional[str] = None):
        if deployment_file is None:
            base_path = (
                Path(__file__).parent / "configuration_files" / "deployment.yaml"
            )
            deployment_file = str(base_path)
        self.deployment_file = deployment_file

    def remove_service(self, service_name: str) -> bool:
        """Remove a service from the deployment configuration."""
        try:
            # Read current deployment file
            with open(self.deployment_file, "r") as f:
                lines = f.readlines()

            # Find and remove the service section
            new_lines = []
            skip_service = False
            current_indent = None

            for line in lines:
                if skip_service:
                    # Check if we're still in the service section
                    if line.strip() == "" or line.startswith("  - name:"):
                        skip_service = False
                        current_indent = None
                    elif current_indent is not None:
                        # Skip lines that are part of this service
                        line_indent = len(line) - len(line.lstrip())
                        if line_indent > current_indent:
                            continue
                        else:
                            skip_service = False
                            current_indent = None

                if (
                    f'name: "{service_name}"' in line
                    or f"name: '{service_name}'" in line
                    or f"name: {service_name}" in line
                ):
                    skip_service = True
                    current_indent = len(line) - len(line.lstrip())
                    continue

                if not skip_service:
                    new_lines.append(line)

            # Write back the modified deployment
            with open(self.deployment_file, "w") as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            print(f"Error removing service {service_name}: {e}")
            return False

    def change_service_instance_type(
        self, service_name: str, from_size: str, to_size: str
    ) -> bool:
        """Change the instance type for services (workshop demonstration)."""
        # For workshop purposes, this simulates changing instance types
        # In real Kubernetes, this would modify resource requests/limits
        print(f"🔧 Simulating instance type change for {service_name}")
        print(f"   From: {from_size} instances → To: {to_size} instances")
        print("   ✅ Instance type migration completed successfully")
        return True


class HistoricalAnalytics:
    """Provides historical analytics for service usage patterns."""

    def __init__(self):
        self._historical_data = self._generate_historical_data()

    def _generate_historical_data(self) -> Dict[str, Dict]:
        """Generate realistic historical data for workshop scenarios."""
        services = [
            "fax-service",
            "price-discovery-service",
            "position-management-service",
            "market-data-service",
            "risk-management-service",
        ]

        data = {}

        for service_name in services:
            service_data = {
                "request_counts": {
                    "30_days": self._generate_request_history(service_name, 30),
                    "90_days": self._generate_request_history(service_name, 90),
                    "180_days": self._generate_request_history(service_name, 180),
                },
                "utilization_history": self._generate_utilization_history(
                    service_name, 180
                ),
            }
            data[service_name] = service_data

        return data

    def _generate_request_history(self, service_name: str, days: int) -> List[Dict]:
        """Generate request count history for a service over specified days."""
        history = []

        for day_offset in range(days):
            date = datetime.now() - timedelta(days=day_offset)

            if service_name == "fax-service":
                # Case A: Zero or near-zero requests over 180 days
                daily_requests = random.randint(0, 0) if day_offset < 30 else 0
            elif service_name == "price-discovery-service":
                # Case B: Consistent but moderate load
                base_requests = random.randint(50000, 80000)
                daily_requests = int(base_requests * random.uniform(0.8, 1.2))
            else:
                # Other services have normal patterns
                base_requests = random.randint(100000, 500000)
                daily_requests = int(base_requests * random.uniform(0.7, 1.3))

            history.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "requests": daily_requests,
                    "errors": int(daily_requests * random.uniform(0.001, 0.01)),
                    "avg_response_time": random.uniform(1, 20),
                }
            )

        return history

    def _generate_utilization_history(self, service_name: str, days: int) -> List[Dict]:
        """Generate CPU/Memory utilization history."""
        history = []

        for day_offset in range(days):
            date = datetime.now() - timedelta(days=day_offset)

            if service_name == "fax-service":
                # Case A: Very low utilization
                cpu_avg = random.uniform(0.5, 2.0)
                memory_avg = random.uniform(1, 5)
            elif service_name == "price-discovery-service":
                # Case B: Suboptimal utilization on large instances
                cpu_avg = random.uniform(15, 25)
                memory_avg = random.uniform(20, 35)
            else:
                # Normal utilization patterns
                cpu_avg = random.uniform(30, 70)
                memory_avg = random.uniform(40, 80)

            history.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "cpu_avg": cpu_avg,
                    "cpu_peak": min(100, cpu_avg * random.uniform(1.2, 2.0)),
                    "memory_avg": memory_avg,
                    "memory_peak": min(100, memory_avg * random.uniform(1.1, 1.5)),
                }
            )

        return history

    def get_service_history(
        self, service_name: str, timeframe: str = "180_days"
    ) -> Dict:
        """Get historical data for a specific service."""
        if service_name in self._historical_data:
            return self._historical_data[service_name]
        return {}

    def get_request_summary(
        self, service_name: str, timeframe: str = "180_days"
    ) -> Dict:
        """Get request count summary for a service."""
        if service_name not in self._historical_data:
            return {"total_requests": 0, "avg_daily": 0, "trend": "unknown"}

        history = self._historical_data[service_name]["request_counts"].get(
            timeframe, []
        )
        if not history:
            return {"total_requests": 0, "avg_daily": 0, "trend": "unknown"}

        total_requests = sum(day["requests"] for day in history)
        avg_daily = total_requests / len(history) if history else 0

        # Calculate trend (comparing first and last week averages)
        if len(history) >= 14:
            recent_avg = sum(day["requests"] for day in history[:7]) / 7
            older_avg = sum(day["requests"] for day in history[-7:]) / 7
            if recent_avg > older_avg * 1.1:
                trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "total_requests": total_requests,
            "avg_daily": avg_daily,
            "trend": trend,
            "timeframe": timeframe,
        }


# Copyright 2025 Bloomberg Finance L.P.
