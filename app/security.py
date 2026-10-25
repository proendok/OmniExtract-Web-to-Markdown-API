from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import get_api_key_details, increment_api_key_usage, check_ip_limit

security_bearer = HTTPBearer(auto_error=False)

def get_client_ip(request: Request) -> str:
    """Extract real client IP considering reverse proxies (Cloudflare, Render, Railway)."""
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

async def authenticate_request(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Dict[str, Any]:
    """
    Authenticates requests via 3 paths:
    1. RapidAPI Marketplace proxy headers
    2. Bearer token / X-API-Key header from our SQLite DB
    3. Free Tier IP-based rate limiting
    """
    # 1. Check RapidAPI Secret
    rapidapi_secret = request.headers.get("X-RapidAPI-Proxy-Secret")
    if rapidapi_secret and settings.RAPIDAPI_PROXY_SECRET and rapidapi_secret == settings.RAPIDAPI_PROXY_SECRET:
        rapid_user = request.headers.get("X-RapidAPI-User", "rapidapi_subscriber")
        return {
            "auth_type": "rapidapi",
            "tier": "rapidapi_plan",
            "identifier": rapid_user,
            "quota_remaining": 999999
        }

    # 2. Extract API Key (either from Bearer or X-API-Key header or query parameter)
    api_key = None
    if bearer and bearer.credentials:
        api_key = bearer.credentials.strip()
    elif request.headers.get("X-API-Key"):
        api_key = request.headers.get("X-API-Key").strip()
    elif request.query_params.get("api_key"):
        api_key = request.query_params.get("api_key").strip()

    if api_key:
        key_data = await get_api_key_details(api_key)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key. Please check your credentials or purchase an API key."
            )
        
        if not key_data["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This API key has been revoked or its subscription has lapsed."
            )
            
        if key_data["requests_this_month"] >= key_data["monthly_limit"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly quota exceeded ({key_data['requests_this_month']}/{key_data['monthly_limit']}). Upgrade your plan to continue."
            )
            
        await increment_api_key_usage(api_key)
        return {
            "auth_type": "api_key",
            "key": api_key,
            "tier": key_data["tier"],
            "requests_used": key_data["requests_this_month"] + 1,
            "monthly_limit": key_data["monthly_limit"],
            "quota_remaining": max(0, key_data["monthly_limit"] - (key_data["requests_this_month"] + 1))
        }

    # 3. Fallback to Free IP-based Demo Tier
    client_ip = get_client_ip(request)
    allowed = await check_ip_limit(client_ip, settings.FREE_TIER_DAILY_LIMIT)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Free daily rate limit of {settings.FREE_TIER_DAILY_LIMIT} requests exceeded for this IP. "
                "Get an API key at /#pricing to get up to 250,000 requests/month."
            )
        )
        
    return {
        "auth_type": "free_ip",
        "ip": client_ip,
        "tier": "free",
        "quota_remaining": "demo_quota"
    }

def verify_admin_key(request: Request) -> bool:
    admin_header = request.headers.get("X-Admin-Key")
    if not admin_header or admin_header != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid administrator key."
        )
    return True
