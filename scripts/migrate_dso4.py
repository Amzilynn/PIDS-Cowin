"""
Migration script — Creates all DSO4 tables in MySQL.

Usage:
    python scripts/migrate_dso4.py

Prerequisites:
    1. Start XAMPP / WAMP and ensure MySQL is running.
    2. Open phpMyAdmin and create a database named  avalive_dso4
       (or set the MYSQL_DB environment variable to your preferred name).
    3. Install the driver:  pip install pymysql sqlalchemy
"""

import sys
import os

# Add project root to path so we can import shared.*
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from shared.database import engine, Base

# Import ALL models so Base.metadata knows about them
from shared.modelsDSO4 import (    # noqa: F401
    DelegueDSO4,
    MedecinDSO4,
    PharmacienDSO4,
    VisiteDSO4,
)


def main():
    print("=" * 60)
    print("  DSO4 — MySQL Migration (Create Tables)")
    print("=" * 60)
    print(f"  Database URL: {engine.url}")
    print()

    try:
        # Create all tables that don't already exist
        Base.metadata.create_all(bind=engine)
        print("  ✅ Tables created successfully:")
        for table_name in Base.metadata.tables:
            print(f"     • {table_name}")
        print()
        print("  Open phpMyAdmin to verify the tables.")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print()
        print("  Troubleshooting:")
        print("    1. Is MySQL running? (check XAMPP Control Panel)")
        print("    2. Does the database 'avalive_dso4' exist in phpMyAdmin?")
        print("    3. Is pymysql installed?  pip install pymysql")
        sys.exit(1)


if __name__ == "__main__":
    main()
