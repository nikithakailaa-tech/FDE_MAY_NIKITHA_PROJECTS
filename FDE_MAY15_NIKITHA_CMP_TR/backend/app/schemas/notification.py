from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationResponse(BaseModel):
    id: int
    message: str
    type: str
    is_read: bool
    complaint_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
