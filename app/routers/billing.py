from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel, EmailStr
from app.config import settings
from app.services.billing import create_checkout_session, handle_stripe_webhook

router = APIRouter(prefix="/v1/billing", tags=["Billing & Payments"])

class CheckoutRequest(BaseModel):
    tier: str  # starter, pro, enterprise
    customer_email: Optional[EmailStr] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

@router.get("/plans")
async def list_plans():
    """List available subscription plans and their limits."""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter Plan",
                "price_usd": 9,
                "billing_period": "month",
                "monthly_requests": settings.STARTER_MONTHLY_LIMIT,
                "features": [
                    "Up to 10,000 requests/month",
                    "Clean Markdown extraction",
                    "OpenGraph & metadata parsing",
                    "LLM token savings analytics",
                    "Standard rate limit (100 req/min)",
                    "Community support"
                ],
                "stripe_enabled": bool(settings.STRIPE_PRICE_STARTER and settings.STRIPE_SECRET_KEY)
            },
            {
                "id": "pro",
                "name": "Pro Developer",
                "price_usd": 29,
                "billing_period": "month",
                "popular": True,
                "monthly_requests": settings.PRO_MONTHLY_LIMIT,
                "features": [
                    "Up to 50,000 requests/month",
                    "All Starter features",
                    "Structured CSS/JSON extraction",
                    "Priority residential proxy pool",
                    "High throughput (300 req/min)",
                    "Direct email support"
                ],
                "stripe_enabled": bool(settings.STRIPE_PRICE_PRO and settings.STRIPE_SECRET_KEY)
            },
            {
                "id": "enterprise",
                "name": "Scale & Enterprise",
                "price_usd": 79,
                "billing_period": "month",
                "monthly_requests": settings.ENTERPRISE_MONTHLY_LIMIT,
                "features": [
                    "Up to 250,000 requests/month",
                    "All Pro features",
                    "Custom rate limit increases",
                    "Dedicated SLA 99.9%",
                    "Webhook alerts & auto-retry",
                    "Priority Slack/Discord support"
                ],
                "stripe_enabled": bool(settings.STRIPE_PRICE_ENTERPRISE and settings.STRIPE_SECRET_KEY)
            }
        ]
    }

@router.post("/checkout")
async def start_checkout(payload: CheckoutRequest):
    """Initiates a Stripe Checkout Session for a selected plan."""
    try:
        tier = payload.tier.lower()
        if tier not in ("starter", "pro", "enterprise"):
            raise HTTPException(status_code=400, detail="Invalid tier. Choose starter, pro, or enterprise.")
            
        session_info = await create_checkout_session(
            tier=tier,
            customer_email=str(payload.customer_email) if payload.customer_email else None,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url
        )
        return {
            "success": True,
            "checkout_url": session_info["checkout_url"],
            "session_id": session_info["session_id"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout initiation failed: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Automated Stripe Webhook for instant provisioning of API keys."""
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header.")
        
    payload = await request.body()
    try:
        result = await handle_stripe_webhook(payload, stripe_signature)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
