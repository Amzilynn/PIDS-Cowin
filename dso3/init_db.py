from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
	sys.path.insert(0, str(WORKSPACE_ROOT))

from dso3.database import Base, engine
from dso3.models import delegate, product, recommendation


def main() -> None:
	Base.metadata.create_all(bind=engine)
	print("DSO3 tables created successfully.")


if __name__ == "__main__":
	main()