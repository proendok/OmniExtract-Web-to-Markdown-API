from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from pydantic import BaseModel, HttpUrl
from app.security import authenticate_request, verify_admin_key
from app.services.scraper import extract_clean_content, fetch_html
from app.database import create_api_key, get_api_key_details
from bs4 import BeautifulSoup

router = APIRouter(prefix="/v1", tags=["API v1"])

class ScrapeRequest(BaseModel):
    url: HttpUrl

class ExtractRequest(BaseModel):
    url: HttpUrl
    selectors: Optional[Dict[str, str]] = None  # e.g. {"headings": "h1, h2", "prices": ".price"}

class CreateKeyRequest(BaseModel):
    tier: str = "starter"
    customer_email: Optional[str] = "admin_generated@omniextract.com"
    monthly_limit: Optional[int] = None

@router.post("/scrape")
async def scrape_post(
    payload: ScrapeRequest,
    auth: Dict[str, Any] = Depends(authenticate_request)
):
    """
    Extract noise-free, token-optimized Markdown and metadata from any URL.
    Returns estimated tokens and token savings percentage.
    """
    try:
        data = await extract_clean_content(str(payload.url))
        return {
            "success": True,
            "data": data,
            "auth": {
                "tier": auth.get("tier"),
                "quota_remaining": auth.get("quota_remaining")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {str(e)}")

@router.get("/scrape")
async def scrape_get(
    url: str = Query(..., description="Target website URL to extract"),
    auth: Dict[str, Any] = Depends(authenticate_request)
):
    """Convenience GET endpoint for rapid testing and simple cURL requests."""
    try:
        data = await extract_clean_content(url)
        return {
            "success": True,
            "data": data,
            "auth": {
                "tier": auth.get("tier"),
                "quota_remaining": auth.get("quota_remaining")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {str(e)}")

@router.post("/extract")
async def extract_structured(
    payload: ExtractRequest,
    auth: Dict[str, Any] = Depends(authenticate_request)
):
    """
    Extract specific CSS selector elements or structured text blocks.
    """
    try:
        raw_html = await fetch_html(str(payload.url))
        soup = BeautifulSoup(raw_html, "lxml")
        results = {}
        
        if payload.selectors:
            for field_name, selector in payload.selectors.items():
                elements = soup.select(selector)
                results[field_name] = [el.get_text(strip=True) for el in elements]
        else:
            # Default extract all headings and links
            results["h1"] = [h.get_text(strip=True) for h in soup.find_all("h1")]
            results["h2"] = [h.get_text(strip=True) for h in soup.find_all("h2")]
            results["links"] = [a.get("href") for a in soup.find_all("a", href=True)][:30]
            
        return {
            "success": True,
            "url": str(payload.url),
            "extracted": results,
            "auth": {
                "tier": auth.get("tier"),
                "quota_remaining": auth.get("quota_remaining")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract structured data: {str(e)}")

@router.get("/usage")
async def check_usage(
    key: str = Query(..., description="Your API Key"),
):
    """Check remaining quota and tier for a given API Key."""
    details = await get_api_key_details(key)
    if not details:
        raise HTTPException(status_code=404, detail="API key not found.")
        
    return {
        "key": f"{key[:8]}...{key[-4:]}",
        "tier": details["tier"],
        "monthly_limit": details["monthly_limit"],
        "requests_this_month": details["requests_this_month"],
        "quota_remaining": max(0, details["monthly_limit"] - details["requests_this_month"]),
        "is_active": bool(details["is_active"]),
        "last_reset_date": details["last_reset_date"]
    }

# ================= Admin Management =================
@router.post("/admin/keys")
async def admin_create_key(
    payload: CreateKeyRequest,
    authorized: bool = Depends(verify_admin_key)
):
    """Admin endpoint to manually generate active API keys."""
    key = await create_api_key(
        tier=payload.tier,
        customer_email=payload.customer_email or "manual@admin",
        custom_limit=payload.monthly_limit
    )
    return {
        "status": "created",
        "key": key,
        "tier": payload.tier,
        "customer_email": payload.customer_email
    }
