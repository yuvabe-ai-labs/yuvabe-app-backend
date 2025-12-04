from pydantic import BaseModel, Field
from typing import Optional, Literal


class PayslipRequestSchema(BaseModel):
    mode: Literal["3_months", "6_months", "manual"]
    start_month: Optional[str] = Field(default=None, description="YYYY-MM")
    end_month: Optional[str] = Field(default=None, description="YYYY-MM")
