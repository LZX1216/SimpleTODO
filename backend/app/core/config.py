# backend/app/core/config.py
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """应用配置类，从环境变量加载配置"""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@db:3306/todo_db"
    )

    # 密钥：用于 JWT token、session 加密等（生产环境必须从环境变量设置）
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    CORS_ORIGINS: list[str] = ["*"]  # 开发阶段允许所有来源，生产环境需严格限制


settings = Settings()