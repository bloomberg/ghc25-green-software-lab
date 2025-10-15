#!/usr/bin/env python3
"""
DO NOT MODIFY
Mock Service - Mock API implementation
Simulates external API calls for workshop exercises.
"""

import time
from typing import Dict, List


def get_single_market_data(symbol: str) -> float:
    """Get equity single market data - SLOW individual API call."""
    print("Opening network connection...")
    time.sleep(1.0)
    print("Requesting data...")
    time.sleep(0.5)  # Simulate slow API call
    print("Closing network connection...")
    time.sleep(0.5)
    # NOTE: Non-realistic prices for example purposes only
    return 100.0 + hash(symbol) % 50


def get_bulk_market_data(requests: List[str]) -> Dict[str, float]:
    """
    FAST bulk API that can handle multiple requests efficiently.

    Args:
        requests: List of tickers
    """
    print("Opening network connection...")
    time.sleep(0.1)  # Bulk API is much faster!
    print("Requesting data...")
    results = {}
    for ticker in requests:
        # NOTE: Non-realistic prices for example purposes only
        results[ticker] = 100.0 + hash(ticker) % 50
    print("Closing network connection...")
    return results


# Copyright 2025 Bloomberg Finance L.P.
