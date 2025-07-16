from pydantic import BaseModel, Field
from typing import Optional

class SignupRequest(BaseModel):
    mobile_number: str = Field(..., pattern=r"^\d{10,15}$")
    password: Optional[str]

class SignupResponse(BaseModel):
    message: str

class SendOTPRequest(BaseModel):
    mobile_number: str

class SendOTPResponse(BaseModel):
    otp: str  # For mock/demo only
    message: str

class VerifyOTPRequest(BaseModel):
    mobile_number: str
    otp: str

class VerifyOTPResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    mobile_number: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class JWTUser(BaseModel):
    id: int
    mobile_number: str
    is_pro: bool
