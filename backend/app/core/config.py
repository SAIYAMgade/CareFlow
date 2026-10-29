import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_DIALECT: str = Field(default="sqlite")  # "oracle" or "sqlite"
    ORACLE_USER: str = Field(default="careflow_admin")
    ORACLE_PASSWORD: str = Field(default="CareFlowSecretPass2026#")
    ORACLE_DSN: str = Field(default="localhost:1521/FREEPDB1")
    ORACLE_CONFIG_DIR: str | None = Field(default=None)
    
    SQLITE_PATH: str = Field(default="./careflow.db")
    
    API_PREFIX: str = Field(default="/api")
    ENVIRONMENT_NAME: str = Field(default="Simulated Clinical Environment (Synthetic Data)")
    DEBUG: bool = Field(default=True)
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")

settings = Settings()
