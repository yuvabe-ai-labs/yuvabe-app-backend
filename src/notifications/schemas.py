from pydantic import BaseModel

class RegisterDeviceRequest(BaseModel):
    device_token: str
    platform: str
    device_model: str
