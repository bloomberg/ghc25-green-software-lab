#!/usr/bin/env python3
"""
Test suite for shared schedule utilities.
"""

from src.yaml_utils import (
    parse_time_to_minutes,
    get_job_duration_minutes,
    check_jobs_overlap,
    find_schedule_conflicts,
)


class TestScheduleUtils:
    """Test shared schedule utility functions."""

    def test_parse_time_to_minutes(self):
        """Test time string parsing to minutes."""
        assert parse_time_to_minutes("00:00") == 0
        assert parse_time_to_minutes("01:30") == 90
        assert parse_time_to_minutes("12:00") == 720
        assert parse_time_to_minutes("23:59") == 1439

    def test_parse_time_single_digit_hour(self):
        """Test parsing time with single digit hour."""
        assert parse_time_to_minutes("2:00") == 120
        assert parse_time_to_minutes("9:30") == 570

    def test_get_job_duration_minutes(self):
        """Test job duration calculation."""
        # Test with hours only
        job = {"duration_hours": 2}
        assert get_job_duration_minutes(job) == 120

        # Test with fractional hours
        job = {"duration_hours": 1.5}
        assert get_job_duration_minutes(job) == 90

        # Test with minutes only
        job = {"duration_minutes": 45}
        assert get_job_duration_minutes(job) == 45

        # Test with both
        job = {"duration_hours": 1, "duration_minutes": 30}
        assert get_job_duration_minutes(job) == 90

        # Test with empty job
        job = {}
        assert get_job_duration_minutes(job) == 0

    def test_check_jobs_overlap_no_overlap(self):
        """Test jobs that don't overlap."""
        # Job 1: 02:00-03:00 (120-180 minutes)
        # Job 2: 03:00-04:00 (180-240 minutes)
        # These are adjacent but don't overlap (end time is exclusive)
        assert not check_jobs_overlap(120, 60, 180, 60)

    def test_check_jobs_overlap_with_overlap(self):
        """Test jobs that do overlap."""
        # Job 1: 02:00-03:30 (120-210 minutes)
        # Job 2: 03:00-04:00 (180-240 minutes)
        # These overlap from 03:00-03:30
        assert check_jobs_overlap(120, 90, 180, 60)

    def test_check_jobs_overlap_contained(self):
        """Test job completely contained in another."""
        # Job 1: 02:00-06:00 (120-360 minutes)
        # Job 2: 03:00-04:00 (180-240 minutes)
        # Job 2 is completely inside Job 1
        assert check_jobs_overlap(120, 240, 180, 60)

    def test_check_jobs_overlap_same_start(self):
        """Test jobs with same start time."""
        # Both start at 02:00
        assert check_jobs_overlap(120, 60, 120, 90)

    def test_find_schedule_conflicts_no_conflicts(self):
        """Test schedule with no conflicts."""
        jobs = [
            {"name": "job1", "start_time": "02:00", "duration_hours": 1},
            {"name": "job2", "start_time": "03:00", "duration_hours": 1},
            {"name": "job3", "start_time": "04:00", "duration_hours": 1},
        ]
        conflicts = find_schedule_conflicts(jobs)
        assert len(conflicts) == 0

    def test_find_schedule_conflicts_with_conflicts(self):
        """Test schedule with conflicts."""
        jobs = [
            {"name": "job1", "start_time": "02:00", "duration_hours": 1.5},
            {"name": "job2", "start_time": "03:00", "duration_hours": 1},
            {"name": "job3", "start_time": "04:30", "duration_hours": 1.5},
        ]
        conflicts = find_schedule_conflicts(jobs)
        assert len(conflicts) == 1
        assert ("job1", "job2") in conflicts

    def test_find_schedule_conflicts_multiple(self):
        """Test schedule with multiple conflicts."""
        jobs = [
            {"name": "job1", "start_time": "02:00", "duration_hours": 2},
            {"name": "job2", "start_time": "03:00", "duration_hours": 2},
            {"name": "job3", "start_time": "03:30", "duration_hours": 1},
        ]
        conflicts = find_schedule_conflicts(jobs)
        # All three jobs overlap in some way
        assert len(conflicts) == 3
        assert ("job1", "job2") in conflicts
        assert ("job1", "job3") in conflicts
        assert ("job2", "job3") in conflicts

    def test_find_schedule_conflicts_empty(self):
        """Test with empty job list."""
        conflicts = find_schedule_conflicts([])
        assert len(conflicts) == 0

    def test_find_schedule_conflicts_single_job(self):
        """Test with single job (no conflicts possible)."""
        jobs = [
            {"name": "job1", "start_time": "02:00", "duration_hours": 1},
        ]
        conflicts = find_schedule_conflicts(jobs)
        assert len(conflicts) == 0


# Copyright 2025 Bloomberg Finance L.P.
