from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    dob: Optional[str] = None
    address: Optional[str] = None

    current_password: Optional[str] = None
    new_password: Optional[str] = None
