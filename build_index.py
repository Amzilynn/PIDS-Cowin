from pathlib import Path
from dotenv import load_dotenv

from app.config import Settings
from app.ingest import build_index


def main() -> None:
    load_dotenv()
    settings = Settings.from_env()
    build_index(Path(settings.docs_dir), Path(settings.index_dir))
    print(f"Index créé avec succès dans: {settings.index_dir}")


if __name__ == "__main__":
    main()