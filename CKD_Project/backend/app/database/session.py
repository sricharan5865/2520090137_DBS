import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Determine database engine arguments & normalize postgresql scheme for Render/Cloud DBs
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Optional MongoDB Client
mongo_client = None
mongo_db = None
if settings.ENABLE_MONGODB:
    try:
        from pymongo import MongoClient
        mongo_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        mongo_db = mongo_client[settings.MONGODB_DB_NAME]
        # Test connection
        mongo_client.admin.command('ping')
        print(f"[MongoDB] Connected to database: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        print(f"[MongoDB] Warning: MongoDB not available ({e}). Flexible notes will use relational storage fallback.")
        mongo_client = None
        mongo_db = None

def get_mongo_db():
    return mongo_db
