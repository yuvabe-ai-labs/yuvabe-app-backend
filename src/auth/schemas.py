from pydantic import BaseModel ,EmailStr
from typing import Optional, Union, Dict


class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str


class VerifyOtpRequest(BaseModel):
    email: str
    otp: str


class LoginRequest(BaseModel):
    email: str
    password: str

class SendVerificationRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: str
    name: str
    email: str


class LoginResponseData(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class BaseResponse(BaseModel):
    code: int
    data: Optional[Union[Dict, str, None]] = None
