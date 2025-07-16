from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User
from app.core import security
from app.services import stripe as stripe_service

router = APIRouter()

# POST /subscribe/pro - Initiate Stripe Checkout
@router.post("/subscribe/pro")
async def subscribe_pro(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(security.oauth2_scheme)
):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    url = await stripe_service.create_checkout_session(user_id)
    return {"checkout_url": url}

# POST /webhook/stripe - Stripe webhook
import os

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    event = None
    # If secret is set, verify signature
    if STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe_service.stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
    else:
        # For local/dev: skip verification
        import json
        try:
            event = stripe_service.stripe.Event.construct_from(
                json.loads(payload), stripe_service.stripe.api_key
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
    # Handle event types
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"]["user_id"])
        q = await db.execute(select(User).where(User.id == user_id))
        user = q.scalar_one_or_none()
        if user:
            user.is_pro = True
            await db.commit()
    return {"status": "success"}

# GET /subscription/status - Check user subscription tier
@router.get("/subscription/status")
async def subscription_status(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(security.oauth2_scheme)
):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"tier": "pro" if user.is_pro else "basic"}
