from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.user import User
from app.core import security
from app.schemas.auth import JWTUser

router = APIRouter()

@router.get("/me", response_model=JWTUser)
async def get_me(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(security.oauth2_scheme)
):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return JWTUser(id=user.id, mobile_number=user.mobile_number, is_pro=user.is_pro)
