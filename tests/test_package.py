"""Test the package imports and metadata."""


def test_package_imports():
    """Test that main package imports work correctly."""
    from src import (
        Service,
        ServiceMetrics,
        ServiceStatus,
        ServiceManager,
        Monitor,
    )

    assert Service is not None
    assert ServiceMetrics is not None
    assert ServiceStatus is not None
    assert ServiceManager is not None
    assert Monitor is not None


# Copyright 2025 Bloomberg Finance L.P.
