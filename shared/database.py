import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Trouver le fichier .env à la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# URL de la base de données (Avalive pour tout le monde)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Valeur par défaut si .env est manquant ou vide
    DATABASE_URL = "mysql+pymysql://root@localhost:3307/avalive"

engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dépendance commune pour obtenir une session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
