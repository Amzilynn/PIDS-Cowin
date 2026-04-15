from __future__ import annotations

import argparse
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
	sys.path.insert(0, str(WORKSPACE_ROOT))

from dso3.database import Base, engine
from dso3.models import delegate, product, recommendation, user


def main() -> None:
	parser = argparse.ArgumentParser(description="Initialize DSO3 database schema")
	parser.add_argument(
		"--reset",
		action="store_true",
		help="Drop existing tables before recreating schema",
	)
	args = parser.parse_args()

	if args.reset:
		Base.metadata.drop_all(bind=engine)
		print("Existing DSO3 tables dropped.")

	Base.metadata.create_all(bind=engine)
	print("DSO3 tables created successfully.")


if __name__ == "__main__":
	main()