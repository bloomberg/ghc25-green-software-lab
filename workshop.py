#!/usr/bin/env python3
"""
Development script to run the workshop service tool.
This is useful for development and testing.
"""

import sys
import os

# Add the src directory to Python path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    from src.cli import main
    main()

# Copyright 2025 Bloomberg Finance L.P.
