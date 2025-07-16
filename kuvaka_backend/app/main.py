import os
from dotenv import load_dotenv
# Always load .env from project root
# Force loading .env from project root (Kuvaka Task/.env), not kuvaka_backend
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from app.api.v1 import auth, user, chatroom, subscription, messages_cleanup
from app.core.error_handling import setup_error_handlers

app = FastAPI()
setup_error_handlers(app)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(chatroom.router, tags=["chatroom"])
app.include_router(subscription.router, tags=["subscription"])
app.include_router(messages_cleanup.router)

# Render free tier: auto-initialize DB if env var set
if os.environ.get("RENDER_DB_INIT") == "1":
    import subprocess
    subprocess.run(["python", "app/db/init_db.py"])
