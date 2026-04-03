"""
Pytest configuration for dso1 tests.
Adds the project root to sys.path so imports resolve correctly.
"""

import sys
from pathlib import Path

# Make sure the project root is on the path
sys.path.insert(0, str(Path(__file__).parents[2]))
