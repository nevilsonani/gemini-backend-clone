import stripe
from fastapi import HTTPException
import os

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
PRO_PRICE_ID = os.getenv("PRO_PRICE_ID")
stripe.api_key = STRIPE_SECRET_KEY

# Create a Stripe Checkout session
async def create_checkout_session(user_id: int):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRO_PRICE_ID,
                "quantity": 1,
            }],
            mode="subscription",
            success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/cancel",
            metadata={"user_id": user_id}
        )
        return session.url
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
