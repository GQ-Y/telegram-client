from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Telegram Client Manager")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "telegram_client")
    SQLALCHEMY_DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dK8x#mP9$vL2@nQ5*hR7^jF3&wY1%cB4!tG6_eZ9")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # WebSocket配置
    WS_HOST: str = os.getenv("WS_HOST", "0.0.0.0")
    WS_PORT: int = int(os.getenv("WS_PORT", "8001"))
    WS_PATH: str = os.getenv("WS_PATH", "/ws")
    WS_PING_INTERVAL: int = int(os.getenv("WS_PING_INTERVAL", "30"))
    WS_PING_TIMEOUT: int = int(os.getenv("WS_PING_TIMEOUT", "10"))
    
    # 应用配置
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    class Config:
        case_sensitive = True

settings = Settings() 