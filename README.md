# Kuvaka Gemini-Style Backend

A scalable, production-ready FastAPI backend for Gemini-style chatrooms with OTP/JWT authentication, Stripe subscriptions, async Gemini integration, Redis caching, and robust error handling.

---

## Table of Contents
- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Setup & Run](#setup--run)
- [Queue System (Celery/Redis)](#queue-system-celeryredis)
- [Gemini API Integration](#gemini-api-integration)
- [Design Decisions & Assumptions](#design-decisions--assumptions)
- [Testing via Postman](#testing-via-postman)
- [Deployment Guide](#deployment-guide)

---

## Features
- **OTP-based JWT Authentication** (mocked OTP)
- **User Chatrooms** (CRUD, per-user isolation)
- **Async Gemini API integration** (via Celery & Redis)
- **Stripe Subscriptions** (Basic/Pro tiers, webhook, status)
- **Rate Limiting** (daily message cap for Basic users)
- **Redis Caching** (chatroom list)
- **Centralized Error Handling** (consistent JSON errors)
- **Environment Variable Config**

---

## Architecture Overview
- **FastAPI**: Main web framework
- **PostgreSQL**: Main DB (async SQLAlchemy)
- **Redis**: Caching & Celery broker
- **Celery**: Async Gemini processing
- **Stripe**: Subscription management
- **Pydantic v2**: Data validation

```
[Client]
   |
[FastAPI Backend] <--- JWT Auth, Stripe, etc.
   |        |
   |        +-- [PostgreSQL] (users, chatrooms, messages)
   |        +-- [Redis] (cache, Celery broker)
   |        +-- [Celery Worker] (async Gemini tasks)
```

---

## Setup & Run

### 1. Clone & Install
```sh
git clone https://github.com/nevilsonani/gemini-backend-clone.git
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file:
```
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/kuvaka
STRIPE_SECRET_KEY=sk_test_...
PRO_PRICE_ID=price_...
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Services
- **Postgres**: Make sure your DB is running and initialized
- **Redis**: `redis-server` (or Memurai on Windows)
- **Celery Worker**: `celery -A celery_worker.celery_app worker -Q gemini --loglevel=info`
- **FastAPI**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

---

## Queue System (Celery/Redis)
- **Celery** offloads Gemini API calls to background workers.
- **Redis** is used as both a cache and the Celery broker.
- When a message is sent, the Gemini task is queued and the DB is updated asynchronously.

---

## Gemini API Integration
- **Currently mocked**: Gemini responses are simulated for demo/testing.
- **To use real Gemini**: Replace the logic in `app/services/gemini.py` with actual API calls and update the async DB update accordingly.

---

## Design Decisions & Assumptions
- OTP is mocked (returned in API response) for dev/testing.
- All endpoints use async SQLAlchemy for scalability.
- Rate limiting is enforced for Basic users only.
- Stripe integration is in test mode (use Stripe test keys).
- Caching is per-user and short-lived for freshness.
- Error handling is centralized for clean API responses.

---

## Testing via Postman
- Import `KuvakaBackend.postman_collection.json` into Postman.
- Use the `jwt_token` variable for all protected endpoints.
- All endpoints are organized by folder for easy navigation.
- Update the base URL if deploying to the cloud.

---

## Deployment Guide

### **Recommended: [Render](https://render.com), [Railway](https://railway.app), or [fly.io](https://fly.io)**
- All support FastAPI, background workers, Postgres, and Redis.
- Deploy FastAPI app, Celery worker, Postgres, and Redis as separate services.
- Expose FastAPI port publicly (e.g., 0.0.0.0:8000)
- Set all environment variables in the cloud dashboard.
- Point Stripe webhook to your public `/webhook/stripe` endpoint.

#### **Example Render Procfile**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A celery_worker.celery_app worker -Q gemini --loglevel=info
```

---

## Access & Deployment Instructions
- After deploying, update your Postman collection base URL.
- Share your public API URL for demo/testing.
- Make sure your Stripe webhook is set to the deployed `/webhook/stripe` URL.


