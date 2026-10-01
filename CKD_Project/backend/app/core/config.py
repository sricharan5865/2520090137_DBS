import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart CKD Risk Prediction & Patient Management System"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Security & CORS
    SECRET_KEY: str = os.getenv("SECRET_KEY", "smart_ckd_super_secret_jwt_key_2026_healthcare_secure_token")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Database configuration (PostgreSQL via DATABASE_URL or local fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./ckd_healthcare.db"
    )
    
    # MongoDB configuration (Optional / semi-structured notes & documents)
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "ckd_healthcare_docs")
    ENABLE_MONGODB: bool = os.getenv("ENABLE_MONGODB", "false").lower() in ("true", "1", "yes")
    
    # Uploads
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))

    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
