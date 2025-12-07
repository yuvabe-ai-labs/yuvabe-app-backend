from pydantic import BaseModel

class RegisterDeviceRequest(BaseModel):
    device_token: str