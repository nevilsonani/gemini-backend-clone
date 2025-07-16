# Kuvaka Gemini Backend

A production-ready FastAPI backend for Gemini-style AI chat, featuring OTP-based login, user-specific chatrooms, async Gemini API conversations, and Stripe-powered subscriptions.

---

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Setup & Installation](#setup--installation)
- [Queue System Explanation](#queue-system-explanation)
- [Gemini API Integration](#gemini-api-integration)
- [Assumptions & Design Decisions](#assumptions--design-decisions)
- [Testing with Postman](#testing-with-postman)
- [Deployment Guide](#deployment-guide)

---

## Features
- **OTP-based user authentication** (mobile, no SMS, OTP returned in API response)
- **JWT-secured endpoints**
- **User-specific chatrooms** (create, list, get details)
- **Async Gemini AI conversations** (via Celery + Redis queue)
- **Stripe-powered subscription management** (Basic/Pro tiers, webhook, status)
- **Rate limiting** for Basic users
- **Redis caching** for chatroom list endpoint
- **Consistent, clean JSON responses and error handling**

---

## Architecture Overview
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Queue:** Celery with Redis (broker & backend)
- **Cache:** Redis (for chatroom list)
- **AI Integration:** Google Gemini API
- **Payments:** Stripe (sandbox)
- **Auth:** JWT with OTP verification

### High-Level Flow
1. User signs up/logs in with OTP (no SMS, OTP returned in API response).
2. JWT is used for all protected endpoints.
3. User creates chatrooms and sends messages.
4. Each message triggers a Celery task for Gemini API response.
5. Stripe manages Pro subscriptions and webhooks.

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- PostgreSQL
- Redis
- Stripe sandbox account
- Google Gemini API key

### 1. Clone the repo
```bash
git clone <your_repo_url>
cd kuvaka_backend
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file at the project root:
```
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/<db>
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=your_google_gemini_api_key
STRIPE_SECRET_KEY=your_stripe_secret
PRO_PRICE_ID=your_stripe_price_id
```

### 4. Initialize the database
```bash
python app/db/init_db.py
```

### 5. Start Redis
```bash
redis-server
```

### 6. Start Celery worker (Windows)
```bash
celery -A app.services.gemini.celery_app worker --pool=solo --loglevel=info
```

### 7. Run the FastAPI server
```bash
uvicorn app.main:app --reload
```

---

## Queue System Explanation
- **Celery** is used as the task queue, with **Redis** as both the broker and backend.
- When a user sends a message, a Celery task is enqueued to call the Gemini API asynchronously.
- The Gemini response is saved to the database when ready.
- This design ensures the API remains responsive and scalable.

---

## Gemini API Integration
- The backend uses the [Google Gemini API](https://ai.google.dev/).
- API key is securely loaded from `.env` and sent in the `x-goog-api-key` header.
- Only free-tier models (e.g., `gemini-2.0-flash`) are used for compatibility.
- Gemini responses are parsed and stored with each message.

---

## Assumptions & Design Decisions
- **OTP is not sent via SMS** (for demo/testing, returned in API response).
- **Chatroom list is cached** per-user in Redis for 30 seconds (performance optimization).
- **Basic users** are limited to 10 messages/day; Pro users are unlimited.
- **Stripe** is sandbox-only; webhooks are for demo/testing.
- **No frontend** is included; API-first design for easy integration.
- **Clean code:** All debug/test logs are removed, only production-level logging remains.

---

## Testing with Postman
- Use the included `KuvakaBackend.postman_collection.json`.
- All endpoints are organized by folder and labeled.
- Use the `/auth/send-otp` and `/auth/verify-otp` flow to get a JWT.
- Set `{{jwt_token}}` variable in Postman for authorized requests.
- Try creating chatrooms, sending messages, and checking Gemini responses (poll `/chatroom/{id}/messages`).
- Use `/subscribe/pro` and `/subscription/status` to test Stripe integration.

---

## Deployment Guide
- The app can be deployed to any public cloud (Render, Railway, EC2, Fly.io, etc.).
- Make sure to set all environment variables in your cloud environment.
- Expose the FastAPI server on a public IP or URL.
- Start Redis and Celery worker on your deployment host.
- Update the Postman collection's base URL to match your deployed endpoint.

---

## Contact & Support
For questions or support, please contact the developer or open an issue in the repository.
