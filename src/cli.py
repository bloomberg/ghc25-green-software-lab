"""Simple command-line interface for the workshop service monitoring tool."""

import argparse
import sys
from pathlib import Path

from src.services import ServiceManager
from src.monitoring import Monitor
from src.yaml_utils import BackupManager, YAMLValidator

from src.cluster_config import HistoricalAnalytics


def create_service_manager_and_monitor() -> tuple:
    """Create and return service manager and monitor instances."""
    service_manager = ServiceManager()
    monitor = Monitor(service_manager)
    return service_manager, monitor


def cmd_status(args) -> None:
    """Show current status of all services."""
    service_manager, monitor = create_service_manager_and_monitor()

    service_list = None
    if args.services:
        service_names = [name.strip() for name in args.services.split(",")]
        service_list = [service_manager.get_service(name) for name in service_names]
        service_list = [s for s in service_list if s is not None]

        if len(service_list) != len(service_names):
            missing = [
                name
                for name in service_names
                if service_manager.get_service(name) is None
            ]
            print(f"Warning: Services not found: {', '.join(missing)}")

    monitor.display_workshop_dashboard(service_list)


def cmd_backup(args) -> None:
    """Manage YAML backups for workshop checkpoints."""
    backup_manager = BackupManager()

    if args.action == "create-checkpoint":
        checkpoint_name = args.checkpoint_name
        print("📁 Creating checkpoint backup...")
        backup_path = backup_manager.create_checkpoint_backup(checkpoint_name)
        if backup_path:
            print(f"✅ Checkpoint created: {backup_path}")

    elif args.action == "restore-checkpoint1-start":
        print("🔄 Restarting to Checkpoint 1 start state...")
        success = backup_manager.restore_original()
        if success:
            print("✅ Successfully reset to Checkpoint 1 start state")
            print("   All manual changes have been reverted")

    elif args.action.startswith("restore-checkpoint"):
        # Handle checkpoint-specific restores
        checkpoint_map = {
            "restore-checkpoint2-start": "checkpoint2-start",  # Checkpoint 2
            "restore-checkpoint3-start": "checkpoint3-start",  # Checkpoint 3
        }

        if args.action in checkpoint_map:
            exercise_id = checkpoint_map[args.action]
            # Map restore command to actual checkpoint number
            checkpoint_display_map = {
                "restore-checkpoint2-start": 2,
                "restore-checkpoint3-start": 3,
            }
            checkpoint_num = checkpoint_display_map[args.action]
            print(f"🔄 Restoring to Checkpoint {checkpoint_num} start state...")
            success = backup_manager.restore_exercise_state(exercise_id)
            if not success:
                print("❌ Restore failed - please check backup files exist")
        else:
            print(f"❌ Unknown restore action: {args.action}")

    elif args.action == "reset-original":
        print("⚠️  INSTRUCTOR ONLY: Reset original backup")
        success = backup_manager.reset_original_backup()
        if success:
            print("✅ Original backup has been reset to current state")

    elif args.action == "list":
        backup_manager.list_backups()

    elif args.action == "status":
        print("📊 Backup Status:")
        print("=" * 30)
        if Path(backup_manager.get_original_backup_path()).exists():
            print("✅ Original backup: Available")
        else:
            print("❌ Original backup: Not found")
        print(f"📁 Backup location: {backup_manager.backup_dir}")
        backup_manager.list_backups()


def cmd_checkpoint(args) -> None:
    """Run checkpoint-related tasks and demos."""
    if args.checkpoint == "2" and args.action == "run-market-data":
        print("🏦 Market Data Service - Checkpoint 2")
        print("=" * 50)

        service_manager, _ = create_service_manager_and_monitor()
        services = service_manager.get_all_services()
        fax_service_exists = any(s.config.name == "fax-service" for s in services)

        if fax_service_exists:
            print("❌ Checkpoint 2 not available")
            print("💡 Complete Checkpoint 1 first")
            return

        print("🐌 Running MARKET DATA SERVICE - this can be slow")

        try:
            from src.market_data_service import run_market_data_analysis

            run_market_data_analysis()
        except KeyboardInterrupt:
            print("\n⏹️  Execution interrupted")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Invalid checkpoint command")
        print("Available commands:")
        print("  python3 workshop.py checkpoint 2 run-market-data")


def cmd_validate(args) -> None:
    """Validate manual changes to deployment.yaml."""
    validator = YAMLValidator()

    # Map validation checkpoint numbers to internal exercise numbers
    checkpoint_to_exercise = {
        1: 1,  # Validate --checkpoint 1 = Checkpoint 1 (fax-service removal)
        2: 2,  # Validate --checkpoint 2 = Checkpoint 2 (performance optimization)
        3: 3,  # Validate --checkpoint 3 = Checkpoint 3 (sustainable scheduling)
    }

    if not args.checkpoint:
        print("❌ Please specify a checkpoint number")
        print("   Usage: python3 workshop.py validate --checkpoint <1|2|3>")
        print("   ")
        print("   Checkpoint 1: Validate fax-service removal (use --checkpoint 1)")
        print("   Checkpoint 2: Validate performance optimization (use --checkpoint 2)")
        print("   Checkpoint 3: Validate sustainable scheduling (use --checkpoint 3)")
        return

    checkpoint_num = args.checkpoint
    exercise_num = checkpoint_to_exercise[checkpoint_num]

    if checkpoint_num == 1:
        target_service = "fax-service"
        task_description = "Smaller Watts, Same Wow - Service removal (fax-service)"

        print(f"🔍 Validating Checkpoint {checkpoint_num}: {task_description}")
        success, message = validator.validate_exercise_completion(
            exercise_num, target_service=target_service
        )
        print(message)

        if success:
            print(f"\n🎉 Checkpoint {checkpoint_num} completed successfully!")
            print("   🔄 Run 'python3 workshop.py status' to see the updated cluster")
        else:
            print("\n💡 Tips:")
            print("   • Edit the file manually:", validator.yaml_file_path)
            print(f"   • Remove only the '{target_service}' service section")
            print("   • Keep all other services unchanged")
            print(
                "   • Use 'python3 workshop.py backup restore-checkpoint1-start' "
                "to start over if needed"
            )

    elif checkpoint_num == 2:
        task_description = (
            "Tracking Down the Code Carbon Culprits - Performance Optimization"
        )

        print(f"🔍 Validating Checkpoint {checkpoint_num}: {task_description}")
        success, message = validator.validate_exercise_completion(exercise_num)
        print(message)

        if success:
            print(f"\n🎉 Checkpoint {checkpoint_num} completed successfully!")
            print("   📈 Performance optimized through bulk API calls")
            print(
                "   🔄 Run 'python3 workshop.py latency' to confirm improved response times"
            )
        else:
            print("\n💡 Next steps:")
            print(
                "   • Edit `getMarketData(api_client)` in the file get_market_data.py to optimize inefficient code"
            )
            print("   • Replace individual API calls with bulk API operations")
            print("   • Look for TODO and inefficient markers in the code")
            print(
                "   • Use 'python3 workshop.py checkpoint 2 run-market-data' to test performance"
            )

    elif checkpoint_num == 3:
        task_description = "Green Light, Go Time - Sustainable Batch Processing"

        print(f"🔍 Validating Checkpoint {checkpoint_num}: {task_description}")
        success, message = validator.validate_exercise_completion(exercise_num)
        print(message)

        if success:
            print(f"\n🎉 Checkpoint {checkpoint_num} completed successfully!")
            print("\n🏆 Workshop Complete! All checkpoints successfully finished!")
        else:
            print("\n💡 Next steps:")
            print(
                "   • Edit schedule.yaml to reschedule jobs to low-carbon periods (2-6AM)"
            )
            print("   • Stagger job start times to avoid resource conflicts")
            print(
                "   • Use 'python3 workshop.py scheduler' to view current job schedule"
            )
            print(
                "   • Use 'python3 workshop.py carbon' to view carbon intensity dashboard"
            )


def cmd_latency(args) -> None:
    """Show latency dashboard for performance analysis."""
    service_manager, monitor = create_service_manager_and_monitor()

    print("\n⚡ LATENCY DASHBOARD")
    print("=" * 60)
    print("Real-time service response time analysis")
    print("=" * 60)

    services = service_manager.get_all_services()

    # Check if Exercise 1 has been completed
    fax_service_exists = any(s.config.name == "fax-service" for s in services)

    if fax_service_exists:
        print("\n❌ LATENCY ANALYSIS NOT AVAILABLE")
        print("-" * 40)
        print("💡 Complete Checkpoint 1 first to unlock latency monitoring")
        print("   Run 'python3 workshop.py status' to see current system state")
        return

    print("\n📊 SERVICE RESPONSE TIMES")
    print("-" * 60)
    print(
        f"{'Service':<20} {'P50 (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Status'}"
    )
    print("-" * 60)

    critical_services = []

    for service in sorted(services, key=lambda x: x.config.name):
        if service.metrics:
            p50 = service.metrics.response_time_p50
            p95 = service.metrics.response_time_p95
            p99 = service.metrics.response_time_p99

            # Determine status based on response times
            # Special handling for market-data service in Checkpoint 3
            if (
                service.config.name == "market-data" and p95 > 10000
            ):  # > 10 seconds for market-data
                status = "🔴 CRITICAL"
                critical_services.append(service.config.name)
            elif p95 > 60000:  # > 1 minute for other services
                status = "🔴 CRITICAL"
                critical_services.append(service.config.name)
            elif p95 > 5000:  # > 5 seconds
                status = "🟡 WARNING"
            else:
                status = "🟢 HEALTHY"

            print(
                f"{service.config.name:<20} {p50:<12.0f} {p95:<12.0f} {p99:<12.0f} {status}"
            )

    if critical_services:
        print("\n🚨 CRITICAL LATENCY ISSUES DETECTED")
        print("=" * 60)
        for service_name in critical_services:
            service = service_manager.get_service(service_name)
            if service and service.metrics:
                avg_response_mins = service.metrics.response_time_p95 / 60000
                print(f"⚠️  {service_name}:")
                print(f"   • Average response time: {avg_response_mins:.1f} minutes")
                print("   • Impact: Severe user experience degradation")
                print(f"   • Queue depth: {service.metrics.queue_depth} requests")

                if service_name == "market-data-service":
                    print("   • 🔍 INVESTIGATION REQUIRED")
                    print(
                        "   • 💡 CHECK: src/get_market_data.py for inefficient code patterns"
                    )
                    print(
                        "   • 📋 SYMPTOMS: Individual API calls instead of bulk operations"
                    )
                    print("   • 🚀 SOLUTION: Refactor to use bulk API endpoints")
                print()

    if critical_services:
        print("\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 40)
        print("- Investigate critical services immediately")
        print("- Review code for inefficient patterns")
        print("- Implement request batching where possible")
        print(
            "- Optimize getMarketData(api_client) in the file get_market_data.py for better performance"
        )

    print()


def cmd_scheduler(args) -> None:
    """Show job schedule dashboard for Checkpoint 4."""
    print("\n📅 JOB SCHEDULE DASHBOARD")
    print("=" * 60)

    # Check if previous Checkpoints are completed
    service_manager, _ = create_service_manager_and_monitor()
    services = service_manager.get_all_services()

    # Check Exercise 1 completion
    fax_service_exists = any(s.config.name == "fax-service" for s in services)
    if fax_service_exists:
        print("\n❌ Scheduler dashboard not available")
        print("💡 Complete Checkpoint 1 first (remove fax-service)")
        return

    # Check Checkpoint 2 completion
    market_data_file = Path("src/get_market_data.py")
    checkpoint_2_completed = False
    if market_data_file.exists():
        content = market_data_file.read_text()
        if "bulk" in content or "batch" in content.lower():
            checkpoint_2_completed = True

    if not checkpoint_2_completed:
        print("\n❌ Advanced scheduler features not available")
        print("💡 Complete Checkpoint 2 first (optimize market-data-service)")
        return

    # Load schedule data
    schedule_file = Path("src/configuration_files/schedule.yaml")

    if not schedule_file.exists():
        print("❌ Schedule configuration not found")
        print("💡 Run setup to initialize schedule.yaml")
        return

    try:
        from src.yaml_utils import read_yaml_file

        schedule_data = read_yaml_file(str(schedule_file))

        jobs = schedule_data.get("jobs", [])

        # Analyze job scheduling
        job_times = {}

        print("🕕 SCHEDULED JOBS:")
        print("-" * 80)
        print(
            f"{'Job Name':<30} | {'Start':<8} | {'Duration':<10} | {'End':<8} | {'Carbon Impact':<15}"
        )
        print("-" * 80)

        for job in jobs:
            name = job.get("name", "Unknown")
            start_time = job.get("start_time", "Unknown")
            duration_hours = job.get("duration_hours", 0)

            # Parse time
            if isinstance(start_time, str) and ":" in start_time:
                time_parts = start_time.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                # Calculate end time properly handling fractional hours
                start_minutes = hour * 60 + minute
                duration_minutes = duration_hours * 60
                end_minutes = start_minutes + duration_minutes
                end_hour = int(end_minutes // 60) % 24
                end_minute = int(end_minutes % 60)

                job_times[name] = {
                    "start": hour,
                    "end": end_hour,
                    "end_minute": end_minute,
                    "duration": duration_hours,
                }

                # Determine the carbon intensity level for a mock region
                if 18 <= hour <= 20:
                    carbon_status = "� HIGH"
                elif 2 <= hour <= 6:
                    carbon_status = "🟢 LOW"
                else:
                    carbon_status = "🟡 MED"

                if duration_hours == int(duration_hours):
                    duration_str = f"{int(duration_hours)}h"
                else:
                    duration_str = f"{duration_hours}h"

                # Format end time with minutes
                end_time_str = f"{end_hour:02d}:{end_minute:02d}"

                print(
                    f"{name:<30} | {start_time:<8} | {duration_str:<10} | {end_time_str:<8} | {carbon_status:<15}"
                )

        print("-" * 80)

        # Resource conflict analysis - check for overlapping execution windows
        print("\n⚠️  RESOURCE CONTENTION ANALYSIS:")
        print("-" * 40)

        # Use shared conflict detection logic
        from src.yaml_utils import find_schedule_conflicts

        conflicts = find_schedule_conflicts(jobs)

        if conflicts:
            for job1_name, job2_name in conflicts:
                # Get job details for display
                job1_details = job_times.get(job1_name, {})
                job2_details = job_times.get(job2_name, {})

                job1_start_time = f"{job1_details.get('start', 0):02d}:00"
                job1_end_time = f"{job1_details.get('end', 0):02d}:{job1_details.get('end_minute', 0):02d}"
                job2_start_time = f"{job2_details.get('start', 0):02d}:00"
                job2_end_time = f"{job2_details.get('end', 0):02d}:{job2_details.get('end_minute', 0):02d}"

                print("🔴 OVERLAP DETECTED:")
                print(f"   • {job1_name}: {job1_start_time} - {job1_end_time}")
                print(f"   • {job2_name}: {job2_start_time} - {job2_end_time}")
                print()
        else:
            print("✅ No resource conflicts detected")
            print("   Jobs are properly staggered across time slots")

        print("💡 RECOMMENDATIONS:")
        print("-" * 40)
        if conflicts:
            print("• Reschedule overlapping jobs to different time slots")
            print("• Consider low-carbon periods (2-6 AM) for batch jobs")
        print("• Use 'python3 workshop.py carbon' to analyze optimal scheduling times")
        print("• Edit schedule.yaml to implement changes")

    except Exception as e:
        print(f"❌ Error loading schedule: {e}")

    print()


def cmd_carbon(args) -> None:
    """Show carbon intensity dashboard for sustainable scheduling."""
    print("\n🌱 CARBON INTENSITY DASHBOARD")
    print("=" * 60)
    print("Power grid composition and optimal scheduling analysis")

    # Check if previous exercises are completed
    service_manager, _ = create_service_manager_and_monitor()
    services = service_manager.get_all_services()

    fax_service_exists = any(s.config.name == "fax-service" for s in services)
    if fax_service_exists:
        print("\n❌ Carbon dashboard not available")
        print("💡 Complete Exercise 1 first (remove fax-service)")
        return

    print("\n🔋 24-HOUR CARBON INTENSITY PROFILE")
    print("-" * 60)

    # Determine the carbon intensity level for a mock region
    carbon_data = {
        18: {
            "level": "HIGH",
            "coal": 40,
            "gas": 30,
            "nuclear": 20,
            "wind": 8,
            "solar": 2,
        },
        19: {
            "level": "HIGH",
            "coal": 42,
            "gas": 28,
            "nuclear": 20,
            "wind": 8,
            "solar": 2,
        },
        20: {
            "level": "HIGH",
            "coal": 38,
            "gas": 32,
            "nuclear": 20,
            "wind": 8,
            "solar": 2,
        },
        22: {
            "level": "MEDIUM",
            "coal": 25,
            "gas": 25,
            "nuclear": 25,
            "wind": 15,
            "solar": 10,
        },
        23: {
            "level": "MEDIUM",
            "coal": 20,
            "gas": 30,
            "nuclear": 25,
            "wind": 20,
            "solar": 5,
        },
        0: {
            "level": "MEDIUM",
            "coal": 22,
            "gas": 28,
            "nuclear": 25,
            "wind": 20,
            "solar": 5,
        },
        2: {
            "level": "LOW",
            "coal": 10,
            "gas": 10,
            "nuclear": 35,
            "wind": 40,
            "solar": 5,
        },
        3: {
            "level": "LOW",
            "coal": 8,
            "gas": 12,
            "nuclear": 35,
            "wind": 40,
            "solar": 5,
        },
        4: {
            "level": "LOW",
            "coal": 5,
            "gas": 15,
            "nuclear": 35,
            "wind": 42,
            "solar": 3,
        },
        5: {
            "level": "LOW",
            "coal": 8,
            "gas": 12,
            "nuclear": 35,
            "wind": 38,
            "solar": 7,
        },
        6: {
            "level": "LOW",
            "coal": 12,
            "gas": 18,
            "nuclear": 30,
            "wind": 30,
            "solar": 10,
        },
    }

    # Fill in remaining hours with interpolated values
    for hour in range(24):
        if hour not in carbon_data:
            if 7 <= hour <= 17:  # Day time
                carbon_data[hour] = {
                    "level": "MEDIUM",
                    "coal": 15,
                    "gas": 20,
                    "nuclear": 30,
                    "wind": 20,
                    "solar": 15,
                }
            elif 21 == hour:  # Transition period
                carbon_data[hour] = {
                    "level": "MEDIUM",
                    "coal": 30,
                    "gas": 25,
                    "nuclear": 25,
                    "wind": 15,
                    "solar": 5,
                }
            else:  # Night time
                carbon_data[hour] = {
                    "level": "MEDIUM",
                    "coal": 18,
                    "gas": 22,
                    "nuclear": 30,
                    "wind": 25,
                    "solar": 5,
                }

    print("Period    | Carbon Level | Coal | Gas  | Nuclear | Wind | Solar |")
    print("-" * 62)

    # Group hours into 2-hour periods (00-02, 02-04, 04-06, etc.)
    for period_start in range(0, 24, 2):
        period_end = (period_start + 2) % 24
        if period_end == 0:
            period_end = 24  # Show as 24 instead of 0 for clarity

        # Calculate average values for the 2-hour period
        data1 = carbon_data[period_start]
        data2 = carbon_data[(period_start + 1) % 24]

        avg_coal = (data1["coal"] + data2["coal"]) // 2
        avg_gas = (data1["gas"] + data2["gas"]) // 2
        avg_nuclear = (data1["nuclear"] + data2["nuclear"]) // 2
        avg_wind = (data1["wind"] + data2["wind"]) // 2
        avg_solar = (data1["solar"] + data2["solar"]) // 2

        # Determine level based on dominant period
        level = (
            data1["level"]
            if data1["level"] == "HIGH" or data2["level"] == "HIGH"
            else (
                "MEDIUM"
                if data1["level"] == "MEDIUM" or data2["level"] == "MEDIUM"
                else "LOW"
            )
        )

        # Color coding
        if level == "HIGH":
            indicator = "🔴"
        elif level == "MEDIUM":
            indicator = "🟡"
        else:
            indicator = "🟢"

        print(
            f"{period_start:02d}:00-{period_end:02d}:00| {indicator} {level:6} | "
            f"{avg_coal:2d}%  | {avg_gas:2d}%  | {avg_nuclear:5d}% | "
            f"{avg_wind:2d}%  | {avg_solar:3d}% |"
        )

    print("\n🎯 OPTIMAL SCHEDULING WINDOWS")
    print("-" * 60)

    print("🟢 LOW CARBON PERIODS (Recommended):")
    print("   • 02:00 - 06:00: 80%+ renewable energy")
    print("   • Best for batch processing jobs")
    print()

    # Current job analysis
    schedule_file = Path("src/configuration_files/schedule.yaml")
    if schedule_file.exists():
        print("📊 CURRENT SCHEDULE CARBON ANALYSIS")
        print("-" * 60)

        try:
            from src.yaml_utils import read_yaml_file

            schedule_data = read_yaml_file(str(schedule_file))

            jobs = schedule_data.get("jobs", [])
            carbon_impact_score = 0

            for job in jobs:
                name = job.get("name", "Unknown")
                start_time = job.get("start_time", "Unknown")
                duration = job.get("duration_hours", 0)

                if isinstance(start_time, str) and ":" in start_time:
                    hour = int(start_time.split(":")[0])
                    level = carbon_data.get(hour, {}).get("level", "UNKNOWN")

                    if level == "HIGH":
                        carbon_impact_score += 3 * duration
                        indicator = "🔴"
                    elif level == "MEDIUM":
                        carbon_impact_score += 2 * duration
                        indicator = "🟡"
                    else:
                        carbon_impact_score += 1 * duration
                        indicator = "🟢"

                    print(f"{indicator} {name}: {start_time} ({level} carbon period)")

            print()
            total_duration = sum(job.get("duration_hours", 0) for job in jobs)
            max_possible_score = total_duration * 3  # All jobs in HIGH periods
            print(
                f"Overall Carbon Impact Score: {carbon_impact_score}/{max_possible_score}"
            )

            # Calculate percentage of max impact
            if max_possible_score > 0:
                impact_percentage = (carbon_impact_score / max_possible_score) * 100

                if impact_percentage > 80:
                    print("❌ HIGH carbon footprint - optimization needed")
                    print("💡 Reschedule jobs to low-carbon periods (2-6 AM)")
                elif impact_percentage > 50:
                    print("🟡 MEDIUM carbon footprint - room for improvement")
                    print("💡 Consider moving some jobs to low-carbon periods")
                else:
                    print("✅ LOW carbon footprint - well optimized!")
            else:
                print("❌ No valid jobs found for carbon analysis")

        except Exception as e:
            print(f"❌ Error analyzing schedule: {e}")

    print("\n💡 OPTIMIZATION RECOMMENDATIONS:")
    print("-" * 60)
    print("• Schedule compute-intensive jobs during 2-6 AM window")
    print("• Stagger job start times to prevent resource conflicts")

    print()


def cmd_software_carbon_intensity(args) -> None:
    """Show software carbon intensity dashboard with energy consumption and emissions data."""
    print("\n🌱 SOFTWARE CARBON INTENSITY DASHBOARD")
    print("=" * 80)
    print(
        "Energy consumption and emissions tracking for the mock trading services cluster"
    )
    print()

    # Analyze current exercise completion state
    exercise_state = _analyze_exercise_completion_state()

    # Generate and display the exercise-based carbon intensity table
    _display_software_carbon_table(exercise_state)

    # Display summary and savings
    _display_exercise_savings_summary(exercise_state)


def _analyze_exercise_completion_state() -> dict:
    """Analyze the current state of workshop exercises to determine optimizations completed."""
    state = {
        "checkpoint_1_complete": False,  # fax-service removed
        "checkpoint_2_complete": False,  # market-data optimization
        "checkpoint_3_complete": False,  # jobs rescheduled
    }

    try:
        # Check Checkpoint 1: fax-service removal
        service_manager, _ = create_service_manager_and_monitor()
        services = service_manager.get_all_services()
        fax_service_exists = any(s.config.name == "fax" for s in services)
        state["checkpoint_1_complete"] = not fax_service_exists

        # Check Checkpoint 2: market-data optimization
        if state["checkpoint_1_complete"]:
            state["checkpoint_2_complete"] = (
                service_manager._check_market_data_optimization()
            )

        # Check Checkpoint 3: job scheduling optimization
        if state["checkpoint_2_complete"]:
            schedule_file = Path("src/configuration_files/schedule.yaml")
            if schedule_file.exists():
                from src.yaml_utils import read_yaml_file

                schedule_data = read_yaml_file(str(schedule_file))
                jobs = schedule_data.get("jobs", [])

                # Check if jobs are rescheduled to low-carbon periods (2-6 AM)
                low_carbon_jobs = 0
                for job in jobs:
                    start_time = job.get("start_time", "")
                    if isinstance(start_time, str) and ":" in start_time:
                        hour = int(start_time.split(":")[0])
                        if 2 <= hour <= 6:  # Low carbon period
                            low_carbon_jobs += 1

                # Consider Checkpoint 3 complete if majority of jobs are in low-carbon periods
                state["checkpoint_3_complete"] = low_carbon_jobs >= len(jobs) // 2

    except Exception as e:
        print(f"Warning: Could not analyze checkpoint state: {e}")

    return state


def _display_software_carbon_table(exercise_state: dict) -> None:
    """Display carbon intensity data in a table showing exercise progression."""

    # ANSI color codes
    BLUE = "\033[94m"
    RESET = "\033[0m"

    print("-" * 110)
    print(
        f"{'Checkpoint':<15} {'Energy (kWh)':<15} {'Carbon Intensity':<20} {'Embodied Carbon':<20} {'SCI':<15} {'Progress':<10}"
    )
    print(f"{'':<15} {'':<15} {'(gCO₂e/kWh)':<20} {'(gCO₂e)':<20} {'':<15} {'':<10}")
    print("-" * 110)

    # Determine the SCI score for mock data
    base_energy = 45.50
    base_carbon_intensity = 425.0
    base_embodied = 12.500
    base_sci = base_energy * base_carbon_intensity + base_embodied

    # Always show baseline
    print(
        f"{'Baseline':<15} {base_energy:<15.2f} {base_carbon_intensity:<20.1f} {base_embodied:<20.3f} {base_sci:<15.1f} {'':<10}"
    )

    # Track previous values for comparison
    prev_energy = base_energy
    prev_carbon_intensity = base_carbon_intensity
    prev_embodied = base_embodied

    # Track progressive values
    current_energy = base_energy
    current_carbon_intensity = base_carbon_intensity
    current_embodied = base_embodied

    # Checkpoint 1: fax service removal
    if exercise_state["checkpoint_1_complete"]:
        current_energy -= 9.1  # -9.1 kWh energy
        current_embodied -= 2.5  # -2.5 kgCO₂e embodied (one machine eliminated)
        current_sci = current_energy * current_carbon_intensity + current_embodied

        # Highlight changed values (except SCI column)
        energy_str = (
            f"{BLUE}{current_energy:<15.2f}{RESET}"
            if current_energy != prev_energy
            else f"{current_energy:<15.2f}"
        )
        embodied_str = (
            f"{BLUE}{current_embodied:<20.3f}{RESET}"
            if current_embodied != prev_embodied
            else f"{current_embodied:<20.3f}"
        )

        print(
            f"{'1':<15} {energy_str} {current_carbon_intensity:<20.1f} {embodied_str} {current_sci:<15.1f} {'🟢⬇':<10}"
        )

        prev_energy = current_energy
        prev_embodied = current_embodied

        # Checkpoint 2: Performance optimization
        if exercise_state["checkpoint_2_complete"]:
            current_energy -= 3.2  # -3.2 kWh (from reduced processing overhead)
            current_energy = 33.30  # Ensure exact value as per requirements
            current_sci = current_energy * current_carbon_intensity + current_embodied

            # Highlight changed values (except SCI column)
            energy_str = (
                f"{BLUE}{current_energy:<15.2f}{RESET}"
                if current_energy != prev_energy
                else f"{current_energy:<15.2f}"
            )

            print(
                f"{'2':<15} {energy_str} {current_carbon_intensity:<20.1f} {current_embodied:<20.3f} {current_sci:<15.1f} {'🟢⬇':<10}"
            )

            prev_energy = current_energy
            prev_carbon_intensity = current_carbon_intensity

            # Checkpoint 3: Sustainable scheduling
            if exercise_state["checkpoint_3_complete"]:
                current_carbon_intensity = 180.0  # 425.0 → 180.0 gCO₂e/kWh
                current_sci = (
                    current_energy * current_carbon_intensity + current_embodied
                )

                # Highlight changed values (except SCI column)
                carbon_str = (
                    f"{BLUE}{current_carbon_intensity:<20.1f}{RESET}"
                    if current_carbon_intensity != prev_carbon_intensity
                    else f"{current_carbon_intensity:<20.1f}"
                )

                print(
                    f"{'3':<15} {current_energy:<15.2f} {carbon_str} {current_embodied:<20.3f} {current_sci:<15.1f} {'🟢⬇':<10}"
                )

    print("-" * 110)


def _display_exercise_savings_summary(exercise_state: dict) -> None:
    """Display summary of carbon savings achieved by each exercise."""
    print()
    print("🎯 CARBON SAVINGS ACHIEVED BY EACH EXERCISE")
    print("=" * 60)

    if exercise_state["checkpoint_1_complete"]:
        print(
            "✅ Checkpoint 1: Eliminated unused fax-service consuming premium machine resources"
        )

        if exercise_state["checkpoint_2_complete"]:
            print("✅ Checkpoint 2: Optimized market-data-service API call patterns")

            if exercise_state["checkpoint_3_complete"]:
                print(
                    "✅ Checkpoint 3: Rescheduled batch jobs from high-carbon to low-carbon periods"
                )

    # Calculate total impact including SCI
    baseline_energy = 45.50
    baseline_embodied = 12.500

    current_energy = baseline_energy
    current_embodied = baseline_embodied

    if exercise_state["checkpoint_1_complete"]:
        current_energy -= 9.1
        current_embodied -= 2.5
        if exercise_state["checkpoint_2_complete"]:
            current_energy = 33.30
            current_embodied = 10.000

    # Next steps aligned with python3 workshop.py status dashboard
    print()
    print("🚀 NEXT STEPS:")
    if not exercise_state["checkpoint_1_complete"]:
        print("   • Complete Checkpoint 1: Remove unused fax-service")
    elif not exercise_state["checkpoint_2_complete"]:
        print("   • Complete Checkpoint 2: Optimize market-data-service performance")
    elif not exercise_state["checkpoint_3_complete"]:
        print("   • Complete Checkpoint 3: Reschedule batch jobs to low-carbon periods")
    else:
        print(
            "   🎉 All exercises complete! Outstanding carbon footprint optimization achieved."
        )


def cmd_historical(args) -> None:
    """Show historical analytics for a service."""
    analytics = HistoricalAnalytics()
    service_name = args.service
    timeframe = args.timeframe

    print(f"\n📊 Historical Analytics: {service_name}")
    print("=" * 60)

    # Get service history
    history = analytics.get_service_history(service_name, timeframe)
    if not history:
        print(f"❌ No historical data found for service: {service_name}")
        return

    # Request summary
    request_summary = analytics.get_request_summary(service_name, timeframe)
    print(f"\n📈 Request Volume Analysis ({timeframe})")
    print("-" * 40)

    print(f"Total Requests: {request_summary['total_requests']:,}")
    print(f"Daily Average: {request_summary['avg_daily']:,.1f}")

    # Recent utilization
    utilization = history.get("utilization_history", [])
    if utilization and len(utilization) >= 7:
        recent_week = utilization[:7]
        avg_cpu = sum(day["cpu_avg"] for day in recent_week) / 7
        avg_memory = sum(day["memory_avg"] for day in recent_week) / 7

        print("\n⚡ Recent Performance (7-day average)")
        print("-" * 40)
        print(f"CPU Utilization: {avg_cpu:.1f}%")
        print(f"Memory Utilization: {avg_memory:.1f}%")

    # Recommendations based on service pattern
    print("\n🔍 Workshop Investigation Notes")
    print("-" * 40)
    if service_name == "fax-service":
        print("• ⚠️  ALERT: Service shows extremely low utilization")
        print("• 🔍 Investigation: Zero request volume detected over 180 days")
        print(
            f"• 💡 Recommendation: {service_name} is unused - remove from deployment.yaml to free resources"
        )
    elif service_name == "price-discovery-service":
        print("• ⚠️  ALERT: Suboptimal resource allocation detected")
        print("• 🔍 Investigation: Consistent moderate load on oversized instances")
        print(
            "• 💡 Recommendation: Migrate from large to small machine size for node2 in deployment.yaml"
        )
    else:
        print("• ✅ Service utilization appears appropriate")
        print("• 📊 No immediate optimization opportunities identified")

    print()


def display_service_summary(service) -> None:
    """Display a summary of a single service."""
    print(f"Service: {service.config.name}")
    print("=" * 50)
    print(f"Type: {service.config.service_type.value}")
    print(f"Status: {service.status.value}")
    print(f"Port: {service.config.port}")
    print(f"Description: {service.description}")

    if service.metrics:
        print("\nCurrent Metrics:")
        print(f"  CPU Usage: {service.metrics.cpu_usage:.1f}%")
        print(
            f"  Memory: {service.metrics.memory_usage:.0f}MB "
            f"({service.metrics.memory_percentage:.1f}%)"
        )
        print(f"  Uptime: {service.get_uptime_display()}")
        print(f"  Requests/sec: {service.metrics.requests_per_second:.1f}")
        print(f"  Response Time (P95): {service.metrics.response_time_p95:.1f}ms")
        print(f"  Error Rate: {service.metrics.error_rate:.2f}%")
        print(f"  Active Connections: {service.metrics.active_connections}")

    health_status = "Healthy" if service.is_healthy() else "Unhealthy"
    print(f"\nHealth: {health_status}")


def main() -> None:
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description="Financial trading venue service monitoring tool - 5-node cluster workshop environment"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    status_parser = subparsers.add_parser(
        "status", help="Show current status of all services"
    )
    status_parser.add_argument(
        "-s",
        "--services",
        help="Comma-separated list of service names to show",
    )
    status_parser.set_defaults(func=cmd_status)

    # Latency command - Show latency dashboard for performance analysis
    latency_parser = subparsers.add_parser(
        "latency", help="Show latency dashboard for performance analysis"
    )
    latency_parser.set_defaults(func=cmd_latency)

    # Scheduler command - Show job schedule dashboard for Checkpoint 3
    scheduler_parser = subparsers.add_parser(
        "scheduler", help="Show job schedule dashboard for resource analysis"
    )
    scheduler_parser.set_defaults(func=cmd_scheduler)

    # Carbon command - Show carbon intensity dashboard for sustainable
    # scheduling
    carbon_parser = subparsers.add_parser(
        "carbon",
        help="Show carbon intensity dashboard for sustainable scheduling",
    )
    carbon_parser.set_defaults(func=cmd_carbon)

    # Software Carbon Intensity command - Show software carbon intensity dashboard
    software_carbon_intensity_parser = subparsers.add_parser(
        "software-carbon-intensity",
        help="Show software carbon intensity dashboard with energy consumption and emissions data",
    )
    software_carbon_intensity_parser.set_defaults(func=cmd_software_carbon_intensity)

    # Historical command - Show historical analytics
    historical_parser = subparsers.add_parser(
        "historical", help="Show historical analytics for a service"
    )
    historical_parser.add_argument("service", help="Name of the service to analyze")
    historical_parser.add_argument(
        "-t",
        "--timeframe",
        default="180_days",
        choices=["30_days", "90_days", "180_days"],
        help="Timeframe for analysis (default: 180_days)",
    )
    historical_parser.set_defaults(func=cmd_historical)

    # Backup command - Manage YAML backups
    backup_parser = subparsers.add_parser(
        "backup", help="Manage deployment.yaml backups for workshop exercises"
    )
    backup_parser.add_argument(
        "action",
        choices=[
            "create-checkpoint",
            "restore-checkpoint1-start",
            "restore-checkpoint2-start",
            "restore-checkpoint3-start",
            "reset-original",
            "list",
            "status",
        ],
        help="Backup action to perform",
    )
    backup_parser.add_argument(
        "--checkpoint-name", help="Name for checkpoint backup (optional)"
    )
    backup_parser.set_defaults(func=cmd_backup)

    # Checkpoint command - Run checkpoint tasks and demos
    checkpoint_parser = subparsers.add_parser(
        "checkpoint", help="Run checkpoint-related tasks and demos"
    )
    checkpoint_parser.add_argument("checkpoint", help="Checkpoint number (e.g., 2)")
    checkpoint_parser.add_argument(
        "action", help="Action to perform (e.g., run-market-data)"
    )
    checkpoint_parser.set_defaults(func=cmd_checkpoint)

    # Validate command - Validate manual YAML changes
    validate_parser = subparsers.add_parser(
        "validate", help="Validate manual changes to deployment.yaml"
    )
    validate_parser.add_argument(
        "--checkpoint",
        type=int,
        choices=[1, 2, 3],
        help="Checkpoint number to validate (1, 2, or 3)",
    )
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Copyright 2025 Bloomberg Finance L.P.
