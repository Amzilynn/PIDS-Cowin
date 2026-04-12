import os
import sys
from pathlib import Path

# Fix path to find session.py
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "dso1/src"))

try:
    from session import load_delegues
    print("Loading delegues...")
    d = load_delegues()
    print(f"Success! Found {len(d)} delegues.")
    for item in d:
        print(item)
except Exception as e:
    print(f"Error: {e}")
