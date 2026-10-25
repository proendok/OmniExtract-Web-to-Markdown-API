from typing import Dict, Any, Optional
import stripe
from app.config import settings
from app.database import create_api_key, revoke_api_key_by_subscription

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_LIMITS = {
    "starter": settings.STARTER_MONTHLY_LIMIT,
    "pro": settings.PRO_MONTHLY_LIMIT,
    "enterprise": settings.ENTERPRISE_MONTHLY_LIMIT
}

def get_price_id_for_tier(tier: str) -> Optional[str]:
    mapping = {
        "starter": settings.STRIPE_PRICE_STARTER,
        "pro": settings.STRIPE_PRICE_PRO,
        "enterprise": settings.STRIPE_PRICE_ENTERPRISE
    }
    return mapping.get(tier.lower())

async def create_checkout_session(
    tier: str,
    customer_email: Optional[str] = None,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None
) -> Dict[str, Any]:
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError(
            "Stripe Secret Key is not configured yet. "
            "Please provide STRIPE_SECRET_KEY in your .env file to activate automated billing."
        )
        
    price_id = get_price_id_for_tier(tier)
    if not price_id:
        raise ValueError(f"No Stripe Price ID configured for tier '{tier}'. Check your .env file.")

    success_redirect = success_url or f"{settings.APP_URL}/checkout-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_redirect = cancel_url or f"{settings.APP_URL}/#pricing"

    session_params: Dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_redirect,
        "cancel_url": cancel_redirect,
        "metadata": {"tier": tier}
    }
    
    if customer_email:
        session_params["customer_email"] = customer_email

    session = stripe.checkout.Session.create(**session_params)
    return {
        "checkout_url": session.url,
        "session_id": session.id
    }

async def handle_stripe_webhook(payload: bytes, sig_header: str) -> Dict[str, Any]:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise ValueError("Stripe Webhook Secret is not configured.")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise ValueError(f"Webhook signature verification failed: {str(e)}")

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    # When a subscription checkout is completed
    if event_type == "checkout.session.completed":
        customer_email = data_object.get("customer_details", {}).get("email") or data_object.get("customer_email", "")
        customer_id = data_object.get("customer", "")
        subscription_id = data_object.get("subscription", "")
        tier = data_object.get("metadata", {}).get("tier", "starter")
        
        # Provision API key automatically!
        api_key = await create_api_key(
            tier=tier,
            customer_email=customer_email,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            custom_limit=PLAN_LIMITS.get(tier, 10000)
        )
        return {"status": "success", "action": "key_created", "api_key": api_key, "email": customer_email}

    # When a subscription is canceled or lapses
    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        subscription_id = data_object.get("id")
        if subscription_id:
            await revoke_api_key_by_subscription(subscription_id)
            return {"status": "success", "action": "key_revoked", "subscription_id": subscription_id}

    return {"status": "ignored", "event_type": event_type}
