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

    # Inefficient: Making separate API calls for each data type
    # TODO there is a bulk api that can do this in one call! api_client.get_bulk_market_data(tickers)
    # =================================================================
    # Inefficient Start
    # =================================================================
    print("📊 Fetching market data using inefficient individual API calls...")
    for ticker in tickers:
        print(f"   🔍 Fetching {ticker} ...")
        market_data[ticker] = api_client.get_single_market_data(ticker)

    # =================================================================
    # Inefficient END
    # =================================================================

    # TODO: Replace the above inefficient loop with bulk API call:
    # market_data = api_client.get_bulk_market_data(tickers)

    return market_data


# Copyright 2025 Bloomberg Finance L.P.
