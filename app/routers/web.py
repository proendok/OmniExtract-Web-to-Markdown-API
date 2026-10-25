from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
import os

router = APIRouter(include_in_schema=False)

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_url": settings.APP_URL,
            "stripe_configured": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_PRICE_STARTER),
            "free_limit": settings.FREE_TIER_DAILY_LIMIT
        }
    )

@router.get("/checkout-success", response_class=HTMLResponse)
async def checkout_success(request: Request, session_id: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "session_id": session_id,
            "app_url": settings.APP_URL
        }
    )

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "OmniExtract API",
        "version": "1.0.0"
    }
