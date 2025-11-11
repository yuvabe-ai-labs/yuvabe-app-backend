from pydantic import BaseModel


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