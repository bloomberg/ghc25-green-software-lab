#!/usr/bin/env python3
"""
Get Market Data - Main data fetching logic
Checkpoint 2: Performance Optimization

This function demonstrates poor API usage patterns that cause
performance bottlenecks in our mock trading system and can be improved with bulk api.
"""

from typing import Dict, Any


def getMarketData(api_client) -> Dict[str, Any]:
    """
    Main market data fetching function

    This function demonstrates poor API usage patterns that cause
    performance bottlenecks in the trading system.
    """

    market_data = {}

    # Data required to fetch
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    market_data = api_client.get_bulk_market_data(tickers)

    return market_data


# Copyright 2025 Bloomberg Finance L.P.
