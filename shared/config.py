"""
Unified system configuration and dynamic pathing.
"""
import os
from pathlib import Path

# Compute the absolute project root dynamically based on this file's position.
# __file__ is shared/config.py, so parent is shared/, parent.parent is Root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Shared Environment Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Absolute path definitions for data storage so modules never use brittle relative paths.
# Example: DSO1_DATA_DIR / "raw" / "video.mp4"
DSO1_DATA_DIR = PROJECT_ROOT / "dso1" / "data"
DSO2_DATA_DIR = PROJECT_ROOT / "dso2" / "data"
