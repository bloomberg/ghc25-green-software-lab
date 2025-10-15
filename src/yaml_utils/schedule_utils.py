"""
Shared utilities for job schedule analysis and conflict detection.
Used by both CLI commands and validation scripts.
"""


def parse_time_to_minutes(time_str):
    """
    Convert HH:MM time string to minutes since midnight.

    Args:
        time_str: Time string in format "HH:MM" or "H:MM"

    Returns:
        int: Minutes since midnight (0-1439)
    """
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + minutes


def get_job_duration_minutes(job):
    """
    Get job duration in minutes from job configuration.

    Args:
        job: Job dictionary with duration_hours and/or duration_minutes

    Returns:
        float: Duration in minutes
    """
    duration = 0.0
    if "duration_hours" in job:
        duration += job["duration_hours"] * 60
    if "duration_minutes" in job:
        duration += job["duration_minutes"]
    return duration


def check_jobs_overlap(
    job1_start_minutes, job1_duration_minutes, job2_start_minutes, job2_duration_minutes
):
    """
    Check if two jobs have overlapping execution windows.

    Args:
        job1_start_minutes: Start time of job 1 in minutes since midnight
        job1_duration_minutes: Duration of job 1 in minutes
        job2_start_minutes: Start time of job 2 in minutes since midnight
        job2_duration_minutes: Duration of job 2 in minutes

    Returns:
        bool: True if jobs overlap, False otherwise

    Algorithm:
        Jobs overlap if: job1_start < job2_end AND job2_start < job1_end
    """
    job1_end = job1_start_minutes + job1_duration_minutes
    job2_end = job2_start_minutes + job2_duration_minutes

    # Check if time ranges overlap
    return job1_start_minutes < job2_end and job2_start_minutes < job1_end


def find_schedule_conflicts(jobs):
    """
    Find all pairs of jobs that have overlapping execution times.

    Args:
        jobs: List of job dictionaries with 'name', 'start_time',
              'duration_hours', and optionally 'duration_minutes'

    Returns:
        list: List of tuples (job1_name, job2_name) representing conflicts
    """
    conflicts = []

    for i, job1 in enumerate(jobs):
        job1_start = parse_time_to_minutes(job1.get("start_time", "00:00"))
        job1_duration = get_job_duration_minutes(job1)

        for job2 in jobs[i + 1 :]:
            job2_start = parse_time_to_minutes(job2.get("start_time", "00:00"))
            job2_duration = get_job_duration_minutes(job2)

            if check_jobs_overlap(job1_start, job1_duration, job2_start, job2_duration):
                conflicts.append((job1["name"], job2["name"]))

    return conflicts
