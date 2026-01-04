import os
from typing import Optional
from pydantic.v1 import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://gptgram:gptgram123@localhost:5432/gptgram"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Vector Store
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "API_KEY")
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv(
        "STRIPE_SECRET_KEY",
        "API_KEY"
    )
    STRIPE_PUBLISHABLE_KEY: str = os.getenv(
        "STRIPE_PUBLISHABLE_KEY",
        "PUBLISHABLE_KEY"
    )
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # n8n Webhook
    N8N_HMAC_SECRET: str = os.getenv("N8N_HMAC_SECRET", "s3cr3t")
    N8N_BASE_URL: str = "https://templatechat.app.n8n.cloud/webhook"
    
    # Feature Flags
    ALLOW_LLM_TRANSFORM: bool = os.getenv("ALLOW_LLM_TRANSFORM", "false").lower() == "true"
    AUTO_APPLY_GAT: bool = os.getenv("AUTO_APPLY_GAT", "true").lower() == "true"
    
    # Limits
    DAILY_TOKEN_LIMIT: int = int(os.getenv("DAILY_TOKEN_LIMIT", "100000"))
    MAX_CHAIN_NODES: int = int(os.getenv("MAX_CHAIN_NODES", "20"))
    DEFAULT_TIMEOUT_MS: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "30000"))
    
    # Platform Settings
    PLATFORM_FEE_PERCENT: int = int(os.getenv("PLATFORM_FEE_PERCENT", "20"))
    MIN_WALLET_TOPUP: int = int(os.getenv("MIN_WALLET_TOPUP", "1000"))
    MAX_WALLET_BALANCE: int = int(os.getenv("MAX_WALLET_BALANCE", "1000000"))
    
    # DAG Execution Settings
    COMPATIBILITY_THRESHOLD: float = float(os.getenv("COMPATIBILITY_THRESHOLD", "0.85"))
    MAX_LLM_RETRY: int = int(os.getenv("MAX_LLM_RETRY", "2"))
    LLM_TEMPERATURE: float = 0.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
