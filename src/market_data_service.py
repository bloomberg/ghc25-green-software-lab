#!/usr/bin/env python3
"""
Market Data Service - Financial Trading Venue Workshop

This file demonstrates intentionally inefficient API call patterns
that workshop attendees will optimize.
"""
import time

from typing import Dict, List, Any
from .mock_service import (
    get_single_market_data as _get_single_market_data,
    get_bulk_market_data as _get_bulk_market_data,
)
from .get_market_data import getMarketData


class MarketDataAPI:
    """Mock API client that simulates external market data service."""

    def __init__(self):
        self.base_url = "https://mock-market-data-api.example.com"
        self.usedOptimized = False

    def get_single_market_data(self, symbol: str) -> float:
        """Get equity spot price - SLOW individual API call."""
        self.usedOptimized = False
        return _get_single_market_data(symbol)

    # The bulk API is much faster
    def get_bulk_market_data(self, requests: List[str]) -> Dict[str, float]:
        """
        FAST bulk API that can handle multiple requests efficiently.

        Args:
            requests: List of tickers
        """
        self.usedOptimized = True
        return _get_bulk_market_data(requests)


def display_market_data(data: Dict[str, Any]) -> None:
    """Display fetched market data in a formatted way."""
    print("\n📈 MARKET DATA RESULTS")
    print("=" * 50)

    for key, value in data.items():
        print(f"📊 {key.replace('_', ' ').title()}:{value}")


def run_market_data_analysis():
    """
    Run market data service performance analysis.
    This function is called by the CLI for Checkpoint 2.
    """
    print("🏦 Market Data Service - Performance Analysis")
    print("=" * 60)
    print("API Performance Optimization Workshop")
    print("=" * 60)

    api_client = MarketDataAPI()

    start_time = time.time()
    print(f"🔄 Starting {getMarketData.__name__}...")
    market_data = getMarketData(api_client)
    end_time = time.time()
    duration = end_time - start_time
    print(f"⏱️  {getMarketData.__name__} completed in {duration:.2f} seconds")

    # Display the results
    display_market_data(market_data)

    print("\n🔍 PERFORMANCE ANALYSIS")
    print("=" * 50)

    if api_client.usedOptimized:
        print("✅ Optimized Implementation:")
        print("   • Uses bulk API calls")
        print("   • Response time: ~0.1 seconds")
        print("   • Reduced server load")
        print("   • Better user experience")
        print("\n🎉 Optimization complete!")
    else:
        print("⚠️  Current Implementation Issues:")
        print("   • Individual API calls in sequence")
        print("   • Response time: ~10 seconds")
        print("   • High server load")
        print("   • Poor user experience")
        print("\n💡 Optimization Opportunity:")
        print("   Consider using the bulk API available in MarketDataAPI")


# Copyright 2025 Bloomberg Finance L.P.
