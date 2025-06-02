from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # Updated import
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Safety check
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()  # Modern SQLAlchemy 2.0 way

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()