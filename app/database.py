import aiosqlite
import datetime
import secrets
from typing import Optional, Dict, Any
from app.config import settings

async def init_db():
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                customer_email TEXT,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                tier TEXT NOT NULL DEFAULT 'starter',
                monthly_limit INTEGER NOT NULL DEFAULT 10000,
                requests_this_month INTEGER NOT NULL DEFAULT 0,
                last_reset_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ip_rate_limits (
                ip_address TEXT PRIMARY KEY,
                request_count INTEGER NOT NULL DEFAULT 0,
                date TEXT NOT NULL
            )
        """)
        await db.commit()

def generate_api_key(tier: str = "starter") -> str:
    prefix = f"omni_{tier[:3]}_"
    token = secrets.token_urlsafe(24)
    return f"{prefix}{token}"

async def create_api_key(
    tier: str,
    customer_email: str = "",
    stripe_customer_id: str = "",
    stripe_subscription_id: str = "",
    custom_limit: Optional[int] = None
) -> str:
    limit_map = {
        "free": settings.FREE_TIER_DAILY_LIMIT * 30,
        "starter": settings.STARTER_MONTHLY_LIMIT,
        "pro": settings.PRO_MONTHLY_LIMIT,
        "enterprise": settings.ENTERPRISE_MONTHLY_LIMIT
    }
    limit = custom_limit or limit_map.get(tier, 10000)
    key = generate_api_key(tier)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO api_keys (
                key, customer_email, stripe_customer_id, stripe_subscription_id,
                tier, monthly_limit, requests_this_month, last_reset_date, created_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 1)
            """,
            (key, customer_email, stripe_customer_id, stripe_subscription_id, tier, limit, today, now)
        )
        await db.commit()
    return key

async def get_api_key_details(key: str) -> Optional[Dict[str, Any]]:
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    current_month = today[:7]

    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM api_keys WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            data = dict(row)
            last_reset_month = data["last_reset_date"][:7]
            
            # Reset monthly quota if a new month started
            if last_reset_month != current_month:
                await db.execute(
                    "UPDATE api_keys SET requests_this_month = 0, last_reset_date = ? WHERE key = ?",
                    (today, key)
                )
                await db.commit()
                data["requests_this_month"] = 0
                data["last_reset_date"] = today
                
            return data

async def increment_api_key_usage(key: str) -> int:
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.execute(
            "UPDATE api_keys SET requests_this_month = requests_this_month + 1 WHERE key = ?",
            (key,)
        )
        await db.commit()
        async with db.execute("SELECT requests_this_month FROM api_keys WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def check_ip_limit(ip_address: str, max_requests: int) -> bool:
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT request_count, date FROM ip_rate_limits WHERE ip_address = ?", (ip_address,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO ip_rate_limits (ip_address, request_count, date) VALUES (?, 1, ?)",
                    (ip_address, today)
                )
                await db.commit()
                return True
            
            if row["date"] != today:
                await db.execute(
                    "UPDATE ip_rate_limits SET request_count = 1, date = ? WHERE ip_address = ?",
                    (today, ip_address)
                )
                await db.commit()
                return True
            
            if row["request_count"] >= max_requests:
                return False
            
            await db.execute(
                "UPDATE ip_rate_limits SET request_count = request_count + 1 WHERE ip_address = ?",
                (ip_address,)
            )
            await db.commit()
            return True

async def revoke_api_key_by_subscription(subscription_id: str):
    async with aiosqlite.connect(settings.DATABASE_PATH) as db:
        await db.execute(
            "UPDATE api_keys SET is_active = 0 WHERE stripe_subscription_id = ?",
            (subscription_id,)
        )
        await db.commit()
