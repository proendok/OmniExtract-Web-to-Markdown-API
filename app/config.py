import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "dev_secret_key_change_me")
    
    # Stripe
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_STARTER: str = os.getenv("STRIPE_PRICE_STARTER", "")
    STRIPE_PRICE_PRO: str = os.getenv("STRIPE_PRICE_PRO", "")
    STRIPE_PRICE_ENTERPRISE: str = os.getenv("STRIPE_PRICE_ENTERPRISE", "")
    
    # RapidAPI
    RAPIDAPI_PROXY_SECRET: str = os.getenv("RAPIDAPI_PROXY_SECRET", "")
    
    # Limits
    FREE_TIER_DAILY_LIMIT: int = int(os.getenv("FREE_TIER_DAILY_LIMIT", "50"))
    STARTER_MONTHLY_LIMIT: int = int(os.getenv("STARTER_MONTHLY_LIMIT", "10000"))
    PRO_MONTHLY_LIMIT: int = int(os.getenv("PRO_MONTHLY_LIMIT", "50000"))
    ENTERPRISE_MONTHLY_LIMIT: int = int(os.getenv("ENTERPRISE_MONTHLY_LIMIT", "250000"))
    
    # Database
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH", 
        "/tmp/omniextract.db" if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "omniextract.db"
    )

settings = Settings()
