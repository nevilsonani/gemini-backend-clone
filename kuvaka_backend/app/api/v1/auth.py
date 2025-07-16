from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.auth import (
    SignupRequest, SignupResponse, SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse, ForgotPasswordRequest, ChangePasswordRequest
)
from app.models.user import User
from app.db.session import get_db
from app.services import otp
from app.core import security
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/signup", response_model=SignupResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    q = await db.execute(select(User).where(User.mobile_number == data.mobile_number))
    user = q.scalar_one_or_none()
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = User(
        mobile_number=data.mobile_number,
        hashed_password=security.get_password_hash(data.password) if data.password else None
    )
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}

@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(data: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.mobile_number == data.mobile_number))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    generated_otp = otp.generate_otp()
    user.otp_secret = generated_otp
    user.otp_expiry = otp.get_expiry()
    await db.commit()
    return {"otp": generated_otp, "message": "OTP sent (mocked)"}

@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(data: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.mobile_number == data.mobile_number))
    user = q.scalar_one_or_none()
    if not user or not user.otp_secret or not user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")
    if user.otp_secret != data.otp or user.otp_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    # Issue JWT
    token = security.create_access_token({"sub": str(user.id), "mobile_number": user.mobile_number, "is_pro": user.is_pro})
    user.otp_secret = None
    user.otp_expiry = None
    await db.commit()
    return {"access_token": token, "token_type": "bearer"}

@router.post("/forgot-password", response_model=SendOTPResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.mobile_number == data.mobile_number))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    generated_otp = otp.generate_otp()
    user.otp_secret = generated_otp
    user.otp_expiry = otp.get_expiry()
    await db.commit()
    return {"otp": generated_otp, "message": "OTP sent for password reset (mocked)"}

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(security.oauth2_scheme)
):
    payload = security.verify_access_token(token)
    user_id = int(payload["sub"])
    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not security.verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    user.hashed_password = security.get_password_hash(data.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}
